/*
 * weiner.c
 *
 * This file finds numerical solutions of the systems listed in examples but
 * implemented in c for speed comparison.
 */

/* Some calls/header files are different for windows */
#if WIN32 | _WIN32 | __WIN32__
    #define WINDOWS 1
#elif __unix__ | __posix__ | __linux__ | __APPLE__
    #define NIX 1
#else
    #error "Unrecognised platform"
#endif

#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <limits.h>
#include <math.h>

/* Random seed uses pid and time in us or ns */
#if WINDOWS
    #include <process.h>
    #include <windows.h>
#else
    #include <unistd.h>
#endif

/* May need defining here */
#ifndef NAN
    #define NAN (0.0 / 0.0)
#endif
#ifndef INFINITY
    #define INFINITY (1.0 / 0.0)
#endif
#ifndef TWOPI
    #define TWOPI 6.2831853071796
#endif

/* Main program routines */
int print_help(char* argv[], char* msg);
int print_weiner();

/* Random number functions */
typedef unsigned long rint_type;
static const rint_type rint_max = ULONG_MAX;
static const double rint_max_double = ULONG_MAX;
void init_rngs(void);
unsigned int initial_seed(void);
rint_type xorshift(void);
double random(void);
double randn_boxmuller(void);


int main(int argc, char *argv[])
{
    int systype;
    int i;

    /* Initialise random seed and prepare for rng generation */
    init_rngs();

    for (i=0; i < 1000000; i++)
        printf("%.15f\n", randn_boxmuller());
    return 0;

    if(argc == 1)
        return print_help(argv, NULL);
    else {
        if(!sscanf(argv[1], "%i", &systype))
            return print_help(argv, "Cannot parse SYSNUM\n");
        switch(systype){
            case 0:
                printf("System %d\n", systype);
                return print_weiner();
            default:
                return print_help(argv, "Invalid SYSNUM\n");
        }
    }

    return 0;
}

int print_help(char *argv[], char *errmsg)
{
    if(errmsg != NULL)
        fprintf(stderr, errmsg);
    printf("usage: %s SYSNUM\n", argv[0]);
    printf("\n");
    printf("Numerically solve the stochastic ordinary differential\n");
    printf("equation representing a Weiner process.\n");
    return 0;
}

int print_weiner()
{
    double x1=0;
    double alpha=0, beta=1;
    double t1=0;
    double t2=1;
    double dt=0.01;

    int nsteps=(int) (t2 - t1) / dt + 1;
    int i;
    double x=x1;
    double t=t1;
    printf("t, x\n");
    printf("%f, %f\n", t1, x1);
    for(i=0; i<nsteps; i++) {
        x += alpha * dt + beta * 0;
        t += dt;
        printf("%f, %f\n", t, x);
    }
    return 0;
}


/*
 * Random number generators.
 *
 * Step 1: good initial seed.
 */

rint_type congruential_next(rint_type seed) {
    return 69069 * seed + 362437;
}

unsigned int initial_seed(void) {
    unsigned int seed, pid, tprec;
#if NIX
    timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    pid = getpid();
    tprec = s.tv_nsec;
#elif WINDOWS
    double microseconds;
    LARGE_INTEGER clockfreq, t;
    if(!QueryPerformanceFrequency(&clockfreq))
        tprec = 0;
    else {
        QueryPerformanceCounter(&t);
        microseconds = (double)t.LowPart / ((double)clockfreq.QuadPart / 1e6);
        tprec = ((unsigned int) microseconds) % 1000000;
    }
    pid = _getpid();
#endif
    seed = congruential_next(time(NULL));
#if NIX | WINDOWS
    seed ^= congruential_next(pid);
    seed ^= congruential_next(tprec);
#endif
    return seed;
}

/*
 * Step 2: good, high-period rngs to generate uniform random numbers on some
 * interval.
 *
 * Taken from Marsaglia:
 * http://groups.google.com/group/comp.lang.c/browse_thread/thread/a9915080a4424068/
 */

/*
 * xor shift generator with a 5d state.
 */

static rint_type _xorshift_x, _xorshift_y, _xorshift_z,
                 _xorshift_w, _xorshift_v;

void xorshift_seed(void) {
    _xorshift_x = rand();
    _xorshift_y = rand();
    _xorshift_z = rand();
    _xorshift_y = rand();
    _xorshift_w = rand();
}

rint_type xorshift(void) {
    rint_type t;
    t=(_xorshift_x^(_xorshift_x>>7));
    _xorshift_x=_xorshift_y;
    _xorshift_y=_xorshift_z;
    _xorshift_z=_xorshift_w;
    _xorshift_w=_xorshift_v;
    _xorshift_v=(_xorshift_v ^ (_xorshift_v <<6 )) ^ (t ^ (t <<13 ));
    return (_xorshift_y + _xorshift_y + 1) * _xorshift_v;
}

/*
 * Set up random seed and initialise rngs.
 */

void init_rngs(void) {
    /* Initialise with system time and iterate a few times */
    srand(initial_seed());

    /* Generate 1 seed so first call doesn't return the sys time */
    rand();

    /* Initialise xorshift array */
    xorshift_seed();
}

/*
 * RNGS Step 2: Generate uniform random numbers in the closed interval [0, 1].
 * We need to map the uniform random numbers to uniform random floating point
 * numbers.
 */

double random(void) {
    return ((double) xorshift()) / rint_max_double;
}

/*
 * RNGS Step 3: Map uniform random floating point numbers to Gaussian
 * distributed numbers.
 */

/*
 * Box Muller method
 *
 * From Jeremy Lea:
 * http://home.online.no/~pjacklam/notes/invnorm/impl/lea/lea.c
 *
 * A normally distributed random number generator. We avoid
 * the uniform rv's being 0.0 since this will result in infinte
 * values, and double count the 0 == 2pi.
 */
double randn_boxmuller() {
    static int i = 1;
    static double u[2] = {0.0, 0.0};
    register double r1, r2, t;

    if (i == 1) {
        t = random();
        if (t == 0)
            t = TWOPI;
        r1 = sqrt(-2*log((double)(t)));
        r2 = TWOPI*(double)random();
        u[0] = r1*sin(r2);
        u[1] = r1*cos(r2);
        i = 0;
    } else {
        i = 1;
    }

    return u[i];
}
