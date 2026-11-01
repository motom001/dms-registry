/* Stubs for functions missing in WASI (no temp files, no processes, no C++ exceptions). */
#include <errno.h>
#include <stdlib.h>
#include <stdio.h>
int mkstemp(char *t) { (void)t; errno = ENOSYS; return -1; }
int system(const char *c) { (void)c; errno = ENOSYS; return -1; }
/* libc++ in wasi-sdk is built without exceptions: a throw ends the module (the host sees a trap). */
void *__cxa_allocate_exception(unsigned long n) { (void)n; fputs("C++-Ausnahme – Abbruch\n", stderr); abort(); }
void __cxa_throw(void *o, void *t, void (*d)(void *)) { (void)o; (void)t; (void)d; abort(); }
