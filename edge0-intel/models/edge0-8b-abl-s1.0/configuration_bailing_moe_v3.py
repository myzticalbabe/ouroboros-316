"""Bailing MoE V2 model configuration"""

from transformers.configuration_utils import PretrainedConfig


class BailingMoeV3Config(PretrainedConfig):

    def __init__(
        self,
        vocab_size=157184,
        hidden_size=2048,
        intermediate_size=5120,
        num_hidden_layers=20,
        num_attention_heads=16,
        num_key_value_heads=4,
        hidden_act="silu",
        use_qkv_bias=False,  # bailing only
        use_bias=False,  # bailing only
        rms_norm_eps=1e-06,
        tie_word_embeddings=False,  # PretrainedConfig key, here change default value.
        embedding_dropout=0.0,
        attention_dropout=0.0,
        output_dropout=0.0,
        initializer_range=0.02,
        max_position_embeddings=32768,
        rope_theta=600000.0,
        use_cache=True,
        max_window_layers=20,
        rope_scaling=None,
        pad_token_id=156892,
        eos_token_id=156892,
        num_experts=256,
        num_shared_experts=1,
        num_experts_per_tok=8,
        n_group=8,
        topk_group=4,
        moe_intermediate_size=512,
        moe_shared_expert_intermediate_size=512,
        first_k_dense_replace=1,
        head_dim=128,
        output_router_logits=False,
        use_qk_norm=True,
        num_nextn_predict_layers=0,
        mtp_loss_scaling_factor=0,
        moe_router_enable_expert_bias=True,
        routed_scaling_factor=1.0,
        layer_group_size=5,
        kv_lora_rank=512,
        q_lora_rank=None,
        qk_rope_head_dim=64,
        v_head_dim=128,
        qk_nope_head_dim=128,
        rope_interleave=True,
        score_function="sigmoid",
        scoring_func="sigmoid",
        seq_aux=True,
        topk_method="noaux_tc",
        router_dtype="fp32",
        gated_attention_proj_granularity_type=None,
        no_kda_lora=False,
        kda_safe_gate=False,
        kda_lower_bound=None,
        short_conv_kernel_size=4,
        pregate_enabled=False,
        pregate_hidden=512,
        pregate_inference=False,
        pregate_use_prev_topk=True,
        pregate_init_router=False,
        pregate_use_prev_token=True,
        pregate_shallow_hidden=1024,
        pregate_shallow_layers=5,
        pregate_shallow_loss_weight=1.5,
        pregate_start_layer=7,
        # v6: cross-token pre-gate.  pregate_N at position t is trained /
        # consumed to route layer N+1 at position t+1 (one-token-ahead),
        # matching the MLX single-sync fast path.  False keeps the v5
        # same-token semantics.
        pregate_cross_token=False,
        # Top-k OPD (on-policy distillation) for the pre-gate modules.
        # strategy: "none" (full-vocab KL, legacy) | "union" | "only_stu" |
        # "only_tch" | "intersection".  The support is always the top-8 expert
        # sets selected by the student pre-gate / teacher router, so the KL is
        # sparse over <=16 experts instead of all 128.
        pregate_opd_strategy="none",
        pregate_opd_topk=8,
        pregate_opd_temperature=1.0,
        pregate_opd_weight=1.0,
        pregate_opd_ce_weight=1.0,
        pregate_opd_weight_mode="teacher_p",
        **kwargs,
    ):
        self.num_hidden_layers = num_hidden_layers
        self.vocab_size = vocab_size
        self.hidden_size = hidden_size
        self.intermediate_size = intermediate_size
        self.num_attention_heads = num_attention_heads
        self.num_key_value_heads = num_key_value_heads
        self.hidden_act = hidden_act
        self.use_qkv_bias = use_qkv_bias
        self.use_bias = use_bias
        self.rms_norm_eps = rms_norm_eps
        self.embedding_dropout = embedding_dropout
        self.attention_dropout = attention_dropout
        self.output_dropout = output_dropout
        self.num_nextn_predict_layers = num_nextn_predict_layers
        self.mtp_loss_scaling_factor = mtp_loss_scaling_factor
        self.initializer_range = initializer_range
        self.max_position_embeddings = max_position_embeddings
        self.rope_theta = rope_theta
        self.use_cache = use_cache
        self.max_window_layers = max_window_layers
        self.head_dim = head_dim or self.hidden_size // self.num_attention_heads
        self.rope_scaling = rope_scaling
        self.use_qk_norm = use_qk_norm
        self.moe_router_enable_expert_bias = moe_router_enable_expert_bias
        self.routed_scaling_factor = routed_scaling_factor

        # MoE configs
        self.num_experts = num_experts
        self.num_shared_experts = num_shared_experts
        self.num_experts_per_tok = num_experts_per_tok
        self.n_group = n_group
        self.topk_group = topk_group
        self.moe_intermediate_size = moe_intermediate_size
        self.moe_shared_expert_intermediate_size = moe_shared_expert_intermediate_size
        self.first_k_dense_replace = first_k_dense_replace
        self.output_router_logits = output_router_logits

        # Linear configs
        self.layer_group_size = layer_group_size
        # mla
        self.kv_lora_rank = kv_lora_rank
        self.q_lora_rank = q_lora_rank
        self.qk_rope_head_dim = qk_rope_head_dim

        self.score_function = score_function
        self.scoring_func = scoring_func
        self.seq_aux = seq_aux
        self.topk_method = topk_method
        self.v_head_dim = v_head_dim
        self.qk_nope_head_dim = qk_nope_head_dim
        self.qk_head_dim = qk_nope_head_dim + qk_rope_head_dim
        self.rope_interleave = rope_interleave
        self.router_dtype = router_dtype
        self.gated_attention_proj_granularity_type = gated_attention_proj_granularity_type
        self.no_kda_lora = no_kda_lora
        self.kda_safe_gate = kda_safe_gate
        self.kda_lower_bound = kda_lower_bound
        self.short_conv_kernel_size = short_conv_kernel_size
        # Pre-gated MoE (arXiv 2308.12066): layer N's pre-gate selects the
        # experts for MoE layer N+1.  pregate_enabled turns the modules on;
        # pregate_inference makes the deployed model use the pre-gate as the
        # router (the first MoE layer keeps its original gate, zero lead).
        self.pregate_enabled = pregate_enabled
        self.pregate_hidden = pregate_hidden
        self.pregate_inference = pregate_inference
        self.pregate_use_prev_topk = pregate_use_prev_topk
        self.pregate_init_router = pregate_init_router
        self.pregate_use_prev_token = pregate_use_prev_token
        self.pregate_shallow_hidden = pregate_shallow_hidden
        self.pregate_shallow_layers = pregate_shallow_layers
        self.pregate_shallow_loss_weight = pregate_shallow_loss_weight
        self.pregate_start_layer = pregate_start_layer
        self.pregate_cross_token = pregate_cross_token
        self.pregate_opd_strategy = pregate_opd_strategy
        self.pregate_opd_topk = int(pregate_opd_topk)
        self.pregate_opd_temperature = float(pregate_opd_temperature)
        self.pregate_opd_weight = float(pregate_opd_weight)
        self.pregate_opd_ce_weight = float(pregate_opd_ce_weight)
        self.pregate_opd_weight_mode = pregate_opd_weight_mode
        super().__init__(
            pad_token_id=pad_token_id, eos_token_id=eos_token_id, tie_word_embeddings=tie_word_embeddings, **kwargs
        )
