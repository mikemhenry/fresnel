// Copyright (c) 2016-2017 The Regents of the University of Michigan
// This file is part of the Fresnel project, released under the BSD 3-Clause License.

#include "VectorMath.h"
#include "ColorMath.h"
#include "Camera.h"

#ifndef __LIGHT_H__
#define __LIGHT_H__

// need to declare these class methods with __device__ qualifiers when building in nvcc
// DEVICE is __host__ __device__ when included in nvcc and blank when included into the host compiler
#undef DEVICE
#ifdef NVCC
#define DEVICE __host__ __device__
#else
#define DEVICE
#endif

namespace fresnel {

//! User Lights
/*! Store user provided light properties. These properties are convenient parameters for users to think about
    and set. The actual device camera properties are derived from these and stored in Lights.

    A single light is defined by a vector that points toward the light (in camera coordinates) and a color.
    Later, the sampling tracer will support area lights.

    The Lights class stores up to 4 lights. They are stored in a fixed size plain old data struct for direct transfer
    to an OptiX variable.

    All of these parameters are directly modifiable as this is a plain old data structure.
*/
struct Lights
    {
    unsigned int N;             //!< Number of lights
    vec3<float> direction[4];   //!< Light directions
    RGB<float> color[4];        //!< Color of each light (linearized sRGB color space)

    //! Default constructor leaves memory uninitialized to support OptiX variables
    Lights() {}

    //! Put lights into scene coordinates given the camera
    explicit Lights(const Lights& lights, const Camera& cam)
        {
        N = lights.N;
        for (unsigned int i = 0; i < N; i++)
            {
            // copy over the color
            color[i] = lights.color[i];

            // normalize direction
            vec3<float> v = lights.direction[i];
            v *= 1.0f / sqrtf(dot(v, v));

            // put direction into scene coordinates
            direction[i] = v.x * cam.r + v.y * cam.u - v.z * cam.d;
            }
        }

    vec3<float> getDirection(unsigned int i)
        {
        return direction[i];
        }

    void setDirection(unsigned int i, const vec3<float>& v)
        {
        direction[i] = v;
        }

    RGB<float> getColor(unsigned int i)
        {
        return color[i];
        }

    void setColor(unsigned int i, const RGB<float>& v)
        {
        color[i] = v;
        }
    };

}
#undef DEVICE

#endif
