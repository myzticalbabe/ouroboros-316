"""Pure-torch fallback for fla KDA kernels (CPU, no triton).

Ports fla/ops/kda/fused_recurrent.py kernel math (decode path):
  l2norm q,k; q*=scale(K^-0.5 default); gk=-5*sigmoid(exp(A)*(g+bias));
  h*=exp(gk); v-=sum(h*k); v*=sigmoid-beta(in); h+=outer(k,v); o=sum(h*q).
State [N,HV,K,V] (STATE_V_FIRST=False). Used for BOTH chunk and fused
entry points (prefill runs recurrent — slower, correct).
"""
import torch


def _softplus(x):
    return torch.log1p(torch.exp(-torch.abs(x))) + torch.clamp(x, min=0)


def torch_kda(q, k, v, g, beta, A_log=None, dt_bias=None, initial_state=None,
              scale=None, output_final_state=False, lower_bound=-5.0,
              reverse=False, cu_seqlens=None, **kw):
    q = q.float(); k = k.float(); v = v.float()
    g = g.float(); beta = beta.float()
    if scale is None:
        scale = k.shape[-1] ** -0.5
    B, T, H, K = q.shape
    HV, V = v.shape[2], v.shape[3]
    if HV != H:
        assert HV % H == 0, f"GVA map needed H={H} HV={HV}"
        rep = HV // H
        q = q.repeat_interleave(rep, dim=2)
        k = k.repeat_interleave(rep, dim=2)
        H = HV
    q = q / (q.norm(dim=-1, keepdim=True) + 1e-6) * scale
    k = k / (k.norm(dim=-1, keepdim=True) + 1e-6)
    A = torch.exp(A_log.float()) if A_log is not None else torch.ones(HV)
    A = A.reshape(1, 1, HV, 1)
    if dt_bias is not None:
        g = g + dt_bias.reshape(1, 1, HV, -1)
    gk = -5.0 * torch.sigmoid(A * g) if lower_bound is not None else -torch.exp(A) * _softplus(g)
    if initial_state is not None:
        h = initial_state.float().reshape(B if cu_seqlens is None else -1, HV, K, V).clone()
        if h.shape[0] == 1 and B > 1:
            h = h.expand(B, -1, -1, -1).clone()
    else:
        Bn = B if cu_seqlens is None else len(cu_seqlens) - 1
        h = torch.zeros(Bn, HV, K, V)
    outs = []
    for t in range(T):
        h = h * torch.exp(gk[:, t].unsqueeze(-1))
        vt = v[:, t] - (h * k[:, t].unsqueeze(-1)).sum(-2)
        vt = vt * beta[:, t].unsqueeze(-1)
        h = h + k[:, t].unsqueeze(-1) * vt.unsqueeze(-2)
        outs.append((h * q[:, t].unsqueeze(-1)).sum(-2))
    o = torch.stack(outs, dim=1)
    fin = h if output_final_state else None
    return o, fin


def _silu(t):
    return t * torch.sigmoid(t)


def _conv_forward(mod, x, cache_state=None):
    # depthwise causal conv1d, fp32 math; x [B,T,D]; cache_state [N,D,W] prepend
    import torch.nn.functional as F
    B, T, D = x.shape
    W = mod.kernel_size[0]
    w = mod.weight.float().reshape(D, 1, W)
    b = mod.bias.float() if mod.bias is not None else None
    if cache_state is not None:
        x = torch.cat([cache_state.transpose(1, 2).to(x.dtype), x], dim=1)
    y = F.conv1d(x.transpose(1, 2).float(), w, None, padding=W - 1, groups=D)[..., :x.shape[1]]
    if b is not None:
        y = y + b.reshape(1, D, 1)
    y = y.transpose(1, 2)
    if mod.activation in ("silu", "swish"):
        y = _silu(y)
    return y


def _torch_step(self, x, residual, cache, output_final_state=False, cu_seqlens=None):
    assert cu_seqlens is None, "varlen unsupported in CPU fallback"
    B, _, D = x.shape
    W = self.kernel_size[0]
    N = B
    if cache is None:
        cache = x.new_zeros(N, D, W)
    cache = cache.roll(shifts=-1, dims=-1)
    cache[..., -1] = x.reshape(N, D)
    w = self.weight.float().reshape(D, W)
    y = (cache * w.unsqueeze(0)).sum(-1).reshape(B, 1, D)
    if self.bias is not None:
        y = y + self.bias.float().reshape(1, 1, D)
    if self.activation in ("silu", "swish"):
        y = _silu(y)
    if residual is not None:
        y = y + residual.reshape(B, 1, D) if residual.dim() == 2 else y + residual
    y = y.to(x.dtype)
    return y, (cache if output_final_state else None)


def _torch_forward(self, x, residual=None, mask=None, cache=None,
                   output_final_state=False, cu_seqlens=None,
                   chunk_indices=None, **kw):
    assert cu_seqlens is None, "varlen unsupported in CPU fallback"
    B, T, D = x.shape
    N = B
    if mask is not None:
        x = x * mask.unsqueeze(-1)
    if B * T == N:
        return _torch_step(self, x, residual, cache, output_final_state)
    init = cache.transpose(1, 2).to(x.dtype) if cache is not None else None
    y = _conv_forward(self, x, init)
    if residual is not None:
        y = y + residual
    final_state = None
    if output_final_state:
        W = self.kernel_size[0]
        full = torch.cat([init, x], dim=1) if init is not None else x
        final_state = full[:, -W:].transpose(1, 2).contiguous()
    return y.to(x.dtype), final_state


def _rms_gated_forward(self, x, g, residual=None, prenorm=False,
                       residual_in_fp32=False):
    assert residual is None and not prenorm, "CPU fallback: no residual/prenorm"
    xf = x.float()
    n = xf * torch.rsqrt(xf.pow(2).mean(-1, keepdim=True) + self.eps)
    if self.weight is not None:
        n = n * self.weight.float()
    gf = g.float()
    gate = torch.sigmoid(gf) if self.activation == "sigmoid" else gf * torch.sigmoid(gf)
    return (n * gate).to(x.dtype)


def install():
    import fla.ops.kda as K
    import fla.ops.kda.chunk as KC
    import fla.ops.kda.fused_recurrent as FR

    def chunk_wrap(*a, **kw):
        return torch_kda(*a, **kw)

    def fused_wrap(*a, **kw):
        return torch_kda(*a, **kw)

    K.chunk_kda = chunk_wrap
    K.fused_recurrent_kda = fused_wrap
    KC.chunk_kda = chunk_wrap
    FR.fused_recurrent_kda = fused_wrap
    from fla.modules.conv.short_conv import ShortConvolution
    ShortConvolution.forward = _torch_forward
    ShortConvolution.step = _torch_step
    from fla.modules.fused_norm_gate import FusedRMSNormGated
    FusedRMSNormGated.forward = _rms_gated_forward
    return True
