/* Ouroboros host: minimal CPython 3.14 embedding (Layer 4 skeleton). */
#include <Python.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

int main(int argc, char** argv) {
    if (argc < 2) {
        fprintf(stderr, "usage: %s <python-code-file>\n", argv[0]);
        return 2;
    }
    FILE* f = fopen(argv[1], "rb");
    if (!f) { perror("fopen"); return 2; }
    fseek(f, 0, SEEK_END);
    long sz = ftell(f);
    fseek(f, 0, SEEK_SET);
    char* buf = (char*)malloc(sz + 1);
    fread(buf, 1, sz, f);
    buf[sz] = '\0';
    fclose(f);

    Py_Initialize();
    /* Run the code; capture via exec in __main__ */
    PyObject* main_mod = PyImport_AddModule("__main__");
    PyObject* globals = PyModule_GetDict(main_mod);
    PyObject* locals = PyDict_New();
    PyObject* code = Py_CompileString(buf, argv[1], Py_file_input);
    if (!code) {
        PyErr_Print();
        Py_Finalize();
        return 1;
    }
    PyObject* res = PyEval_EvalCode(code, globals, locals);
    if (!res) {
        PyErr_Print();
        Py_Finalize();
        return 1;
    }
    /* If a 'result' variable exists, print it */
    PyObject* result = PyDict_GetItemString(locals, "result");
    if (!result) result = PyDict_GetItemString(globals, "result");
    if (result) {
        PyObject* repr = PyObject_Repr(result);
        const char* s = PyUnicode_AsUTF8(repr);
        printf("RESULT: %s\n", s ? s : "<unprintable>");
        Py_DECREF(repr);
    } else {
        printf("OK (no 'result' variable)\n");
    }
    Py_DECREF(res);
    Py_DECREF(locals);
    Py_DECREF(code);
    Py_Finalize();
    free(buf);
    return 0;
}