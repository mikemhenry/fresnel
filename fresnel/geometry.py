# Copyright (c) 2016-2018 The Regents of the University of Michigan
# This file is part of the Fresnel project, released under the BSD 3-Clause License.

R"""
Geometric primitives.

:py:class:`Geometry` provides operations common to all geometry classes. Use a specific geometry class to add objects
to the :py:class:`fresnel.Scene`.

.. seealso::
    :doc:`examples/001-Primitive-properties`
        Tutorial: Modifying primitive properties.

    :doc:`examples/002-Material-properties`
        Tutorial: Modifying material properties.

    :doc:`examples/003-Outline-materials`
        Tutorial: Applying outline materials.

    :doc:`examples/200-Multiple-geometries`
        Tutorial: Displaying multiple geometries in a scene.
"""

from . import material
from . import util
import numpy

class Geometry(object):
    R""" Base class for all geometry.

    :py:class:`Geometry` provides operations common to all geometry classes.

    Attributes:
        material (:py:class:`fresnel.material.Material`): The geometry's material.
        outline_material (:py:class:`fresnel.material.Material`): The geometry's outline material.
        outline_width (`float`): The geometry's outline width, in distance units in the scene's coordinate system.

    Note:

        You cannot instantiate a Geometry directly. Use one of the sub classes.

    """
    def __init__(self):
        raise RuntimeError("Use a specific geometry class");

    def enable(self):
        R""" Enable the geometry.

        When enabled, the geometry will be present when rendering the scene.
        """

        self._geometry.enable();

    def disable(self):
        R""" Disable the geometry.

        When disabled, the geometry will not be present in the scene.
        """

        self._geometry.disable();

    def remove(self):
        R""" Remove the geometry from the scene.

        After calling remove, the geometry is no longer part of the scene. It cannot be added back into the scene.
        Use :py:meth:`disable` if you want a reversible operation.
        """
        self._geometry.remove();
        self.scene.geometry.remove(self)

    @property
    def material(self):
        return material._material_proxy(self);

    @material.setter
    def material(self, mat):
        self._geometry.setMaterial(mat._get_cpp_material());

    @property
    def outline_material(self):
        return material._outline_material_proxy(self);

    @outline_material.setter
    def outline_material(self, mat):
        self._geometry.setOutlineMaterial(mat._get_cpp_material());

    @property
    def outline_width(self):
        return self._geometry.getOutlineWidth();

    @outline_width.setter
    def outline_width(self, width):
        self._geometry.setOutlineWidth(width);

class Cylinder(Geometry):
    R""" Cylinder geometry.

    Define a set of spherocylinder primitives with start and end positions, radii, and individual colors.

    Args:
        scene (:py:class:`fresnel.Scene`): Add the geometry to this scene
        points (`numpy.ndarray` or `array_like`): (``Nx2x3`` : ``float32``) - cylinder start and end points.
        radius (`numpy.ndarray` or `array_like`): (``N`` : ``float32``) - Radius of each cylinder.
        color (`numpy.ndarray` or `array_like`): (``Nx2x3`` : ``float32``) - Color of each start and end point.
        N (int): Number of cylinders in the geometry. If ``None``, determine ``N`` from *points*.

    .. seealso::
        :doc:`examples/101-Cylinder-geometry`
            Tutorial: defining and setting cyliner geometry properties

    Note:
        The constructor arguments ``points``, ``radius``, and ``color`` are optional. If you do not provide them,
        they are initialized to 0's.

    .. hint::
        Avoid costly memory allocations and type conversions by specifying primitive properties in the appropriate
        numpy array type.

    .. tip::
        When all cylinders are the same size, pass a single value for *radius* and numpy will broadcast it to all
        elements of the array.

    Attributes:
        points (:py:class:`fresnel.util.array`): Read or modify the start and end points of the cylinders.
        radius (:py:class:`fresnel.util.array`): Read or modify the radii of the cylinders.
        color (:py:class:`fresnel.util.array`): Read or modify the colors of the start and end points of the cylinders.
    """

    def __init__(self,
                 scene,
                 points=None,
                 radius=None,
                 color=None,
                 N=None,
                 material=material.Material(solid=1.0, color=(1,0,1)),
                 outline_material=material.Material(solid=1.0, color=(0,0,0)),
                 outline_width=0.0):
        if N is None:
            N = len(points);

        self._geometry = scene.device.module.GeometryCylinder(scene._scene, N);
        self.material = material;
        self.outline_material = outline_material;
        self.outline_width = outline_width;

        if points is not None:
            self.points[:] = points;

        if radius is not None:
            self.radius[:] = radius;

        if color is not None:
            self.color[:] = color;

        self.scene = scene;
        self.scene.geometry.append(self);

    def get_extents(self):
        R""" Get the extents of the geometry

        Returns:
            [[minimum x, minimum y, minimum z],[maximum x, maximum y, maximum z]]
        """
        A = self.points[:,0];
        B = self.points[:,1];
        r = self.radius[:];
        r = r.reshape(len(r),1);
        res = numpy.array([numpy.min([numpy.min(A - r, axis=0), numpy.min(B - r, axis=0)], axis=0),
                           numpy.max([numpy.max(A + r, axis=0), numpy.max(B + r, axis=0)], axis=0)])
        return res;


    @property
    def points(self):
        return util.array(self._geometry.getPointsBuffer(), geom=self)

    @property
    def radius(self):
        return util.array(self._geometry.getRadiusBuffer(), geom=self)

    @property
    def color(self):
        return util.array(self._geometry.getColorBuffer(), geom=self)

class Prism(Geometry):
    R""" Prism geometry.

    Define a set of right convex prism primitives. The bottom polygon face is always in the xy plane. Each prism may
    have a different height and rotation angle.

    Args:
        scene (:py:class:`fresnel.Scene`): Add the geometry to this scene
        vertices: The vertices of the polygon in a counter clockwise winding direction.
          **Type:** anything convertible by numpy to a Nx2 array of floats.
        position: Positions of the prisms, *optional*.
          **Type:** anything convertible by numpy to a Nx3 array of floats.
        height: Height of each prism in the z direction, *optional*.
          **Type:** anything convertible by numpy to a N length array of floats.
        angle: Rotation angle of each prism (in radians), *optional*.
          **Type:** anything convertible by numpy to a N length array of floats.
        color: (r,g,b) color of each particle, *optional*.
          **Type:** anything convertible by numpy to a Nx3 array of floats.
        N (int): Number of prisms in the geometry. If ``None``, determine ``N`` from ``position``.

    Note:
        The constructor arguments ``position``, ``height``, ``angle``, and ``color`` are optional, and just short-hand
        for assigning the attribute after construction.

    Colors are in the linearized sRGB color space. Use :py:func:`fresnel.color.linear` to convert standard sRGB colors
    into this space.

    .. hint::
        Avoid costly memory allocations and type conversions by specifying primitive properties in the appropriate
        numpy array type.

    Attributes:
        position (:py:class:`fresnel.util.array`): Read or modify the positions of the prisms.
        height (:py:class:`fresnel.util.array`): Read or modify the heights of the prisms.
        angle (:py:class:`fresnel.util.array`): Read or modify the angles of the prisms.
        color (:py:class:`fresnel.util.array`): Read or modify the color of the prisms.

    """

    def __init__(self,
                 scene,
                 vertices,
                 position=None,
                 angle=None,
                 height=None,
                 color=None,
                 N=None,
                 material=material.Material(solid=1.0, color=(1,0,1)),
                 outline_material=material.Material(solid=1.0, color=(0,0,0)),
                 outline_width=0.0):
        if N is None:
            N = len(position);

        self._geometry = scene.device.module.GeometryPrism(scene._scene, vertices, N);
        self.material = material;
        self.outline_material = outline_material;
        self.outline_width = outline_width;

        if position is not None:
            self.position[:] = position;

        if height is not None:
            self.height[:] = height;

        if angle is not None:
            self.angle[:] = angle;

        if color is not None:
            self.color[:] = color;

        self.scene = scene;
        self.scene.geometry.append(self);

    @property
    def position(self):
        return util.array(self._geometry.getPositionBuffer(), geom=self)

    @property
    def height(self):
        return util.array(self._geometry.getHeightBuffer(), geom=self)

    @property
    def angle(self):
        return util.array(self._geometry.getAngleBuffer(), geom=self)

    @property
    def color(self):
        return util.array(self._geometry.getColorBuffer(), geom=self)

class Sphere(Geometry):
    R""" Sphere geometry.

    Define a set of sphere primitives with positions, radii, and individual colors.

    Args:
        scene (:py:class:`fresnel.Scene`): Add the geometry to this scene
        position (`numpy.ndarray` or `array_like`): (``Nx3`` : ``float32``) -  Positions of each sphere.
        radius (`numpy.ndarray` or `array_like`): (``N`` : ``float32``) - Radius of each sphere.
        color (`numpy.ndarray` or `array_like`): (``Nx3`` : ``float32``) - Color of each sphere.
        N (int): Number of spheres in the geometry. If ``None``, determine ``N`` from ``position``.

    .. seealso::
        :doc:`examples/100-Sphere-geometry`
            Tutorial: Defining and setting sphere geometry properties.

    Note:
        The constructor arguments ``position``, ``radius``, and ``color`` are optional. If you do not provide them,
        they are initialized to 0's.

    .. hint::
        Avoid costly memory allocations and type conversions by specifying primitive properties in the appropriate
        numpy array type.

    .. tip::
        When all spheres are the same size, pass a single value for *radius* and numpy will broadcast it to all
        elements of the array.

    Attributes:
        position (:py:class:`fresnel.util.array`): Read or modify the positions of the spheres.
        radius (:py:class:`fresnel.util.array`): Read or modify the radii of the spheres.
        color (:py:class:`fresnel.util.array`): Read or modify the color of the spheres.
    """

    def __init__(self,
                 scene,
                 position=None,
                 radius=None,
                 color=None,
                 N=None,
                 material=material.Material(solid=1.0, color=(1,0,1)),
                 outline_material=material.Material(solid=1.0, color=(0,0,0)),
                 outline_width=0.0):
        if N is None:
            N = len(position);

        self._geometry = scene.device.module.GeometrySphere(scene._scene, N);
        self.material = material;
        self.outline_material = outline_material;
        self.outline_width = outline_width;

        if position is not None:
            self.position[:] = position;

        if radius is not None:
            self.radius[:] = radius;

        if color is not None:
            self.color[:] = color;

        self.scene = scene;
        self.scene.geometry.append(self);

    def get_extents(self):
        R""" Get the extents of the geometry

        Returns:
            [[minimum x, minimum y, minimum z],[maximum x, maximum y, maximum z]]
        """
        pos = self.position[:];
        r = self.radius[:];
        r = r.reshape(len(r),1);
        res = numpy.array([numpy.min(pos - r, axis=0),
                           numpy.max(pos + r, axis=0)])
        return res;


    @property
    def position(self):
        return util.array(self._geometry.getPositionBuffer(), geom=self)

    @property
    def radius(self):
        return util.array(self._geometry.getRadiusBuffer(), geom=self)

    @property
    def color(self):
        return util.array(self._geometry.getColorBuffer(), geom=self)

class Mesh(Geometry):
    R""" Mesh geometry.

    Define a set of triangle mesh primitives.

    Args:
        scene (:py:class:`fresnel.Scene`): Add the geometry to this scene
        vertices: The vertices of the triangles, in contiguous representation
          **Type:** anything convertible by numpy to a Nvertsx3 array of floats.
          [[tri0a_x, tri0a_y, tri0a_z], [tri0b_x, ..], [tri0c_x, ..], [tri1a_x, ..], ..]
        colors: (r,g,b) color of each vertex, *optional*.
          **Type:** anything convertible by numpy to a Nx3 array of floats.
        position: Positions of the triangle meshes, *optional*.
          **Type:** anything convertible by numpy to a Nx3 array of floats.
        orientation: Orientation quaternion angle of each triangle mesh, *optional*.
          **Type:** anything convertible by numpy to a Nx4 length array of floats.
        N (int): Number of triangle meshes in the geometry. If ``None``, determine ``N`` from ``position``.
    Note:
        The constructor arguments ``position``, ``orientation``, and ``color`` are optional, and just short-hand
        for assigning the attribute after construction.

    Colors are in the linearized sRGB color space. Use :py:func:`fresnel.color.linear` to convert standard sRGB colors
    into this space. :py:class:`fresnel.geometry.mesh` determines the color of a triangle using interpolation
    with the barycentric coordinates in every triangular face.

    .. hint::
        Avoid costly memory allocations and type conversions by specifying primitive properties in the appropriate
        numpy array type.

    Attributes:
        position (:py:class:`fresnel.util.array`): Read or modify the positions of the triangle meshes.
        orientation (:py:class:`fresnel.util.array`): Read or modify the orientations of the triangle meshes.
        colors (:py:class:`fresnel.util.array`): Read or modify the color of the meshes.
    """

    def __init__(self,
                 scene,
                 vertices,
                 position=None,
                 orientation=None,
                 colors=None,
                 N=None,
                 material=material.Material(solid=1.0, color=(1,0,1)),
                 outline_material=material.Material(solid=1.0, color=(0,0,0)),
                 outline_width=0.0):
        if N is None:
            N = len(position);

        self.vertices = numpy.asarray(vertices,dtype=numpy.float32)
        self._geometry = scene.device.module.GeometryMesh(scene._scene, self.vertices, N);
        self.material = material;
        self.outline_material = outline_material;
        self.outline_width = outline_width;

        if position is not None:
            self.position[:] = position;

        if orientation is not None:
            self.orientation[:] = orientation;

        if colors is not None:
            self.colors[:] = colors;

        self.scene = scene;
        self.scene.geometry.append(self);

    @property
    def position(self):
        return util.array(self._geometry.getPositionBuffer(), geom=self)

    @property
    def orientation(self):
        return util.array(self._geometry.getOrientationBuffer(), geom=self)

    @property
    def colors(self):
        return util.array(self._geometry.getColorBuffer(), geom=self)

    def get_extents(self):
        R""" Get the extents of the geometry

        Returns:
            [[minimum x, minimum y, minimum z],
             [maximum x, maximum y, maximum z]]
        """
        a = self.vertices[:,0];
        b = self.vertices[:,1];
        c = self.vertices[:,2];
        r = numpy.array([numpy.min([numpy.min(a, axis=0), numpy.min(b, axis=0), numpy.min(c, axis=0)], axis=0),
                           numpy.max([numpy.max(a, axis=0), numpy.max(b, axis=0), numpy.max(c, axis=0)], axis=0)])

        pos = self.position[:];
        res = numpy.array([numpy.min(pos + r[0], axis=0),
                           numpy.max(pos + r[1], axis=0)])
        return res;

#--------------------------------------------------------------

class ConvexPolyhedron(Geometry):
    R""" Convex polyhedron geometry.

    Define a set of convex polyhedron primitives. A convex polyhedron is defined by *P* outward facing planes
    (origin and normal vector) and a radius that encompass the shape.
    :py:func:`fresnel.util.convex_polyhedron_from_vertices` can construct this by computing the convex hull of a set
    of vertices.

    Args:
        scene (:py:class:`fresnel.Scene`): Add the geometry to this scene
        polyhedron_info (`dict`): A dictionary containing the face normals (``face_normal``), origins (``face_origin``),
            colors (``face_color``), and the radius (``radius``)).
        position (`numpy.ndarray` or `array_like`): (``Nx3`` : ``float32``) -  Position of each polyhedra.
        orientation (`numpy.ndarray` or `array_like`): (``Nx4`` : ``float32``) -  Orientation of each polyhedra (as a quaternion).
        color (`numpy.ndarray` or `array_like`): (``Nx3`` : ``float32``) - Color of each polyhedron.
        N (int): Number of spheres in the geometry. If ``None``, determine ``N`` from ``position``.

    .. seealso::
        :doc:`examples/102-Convex-polyhedron-geometry`
            Tutorial: Defining and setting convex polyhedron geometry properties.

    Note:
        The constructor arguments ``position``, ``orientation``, and ``color`` are optional. If you do not provide them,
        they are initialized to 0's.

    .. hint::
        Avoid costly memory allocations and type conversions by specifying primitive properties in the appropriate
        numpy array type.

    Attributes:
        position (:py:class:`fresnel.util.array`): Read or modify the positions of the polyhedra.
        orientation (:py:class:`fresnel.util.array`): Read or modify the orientations of the polyhedra.
        color (:py:class:`fresnel.util.array`): Read or modify the color of the polyhedra.
        color_by_face (float): Set to 0 to color particles by the per-particle color. Set to 1 to color faces by the per-face color. Set to a value between 0 and 1 to blend per-particle and per-face colors.

    """

    def __init__(self,
                 scene,
                 polyhedron_info,
                 position=None,
                 orientation=None,
                 color=None,
                 N=None,
                 material=material.Material(solid=1.0, color=(1,0,1)),
                 outline_material=material.Material(solid=1.0, color=(0,0,0)),
                 outline_width=0.0):
        if N is None:
            N = len(position);


        origins = polyhedron_info['face_origin']
        normals = polyhedron_info['face_normal']
        face_colors = polyhedron_info['face_color']
        r = polyhedron_info['radius']
        self._geometry = scene.device.module.GeometryConvexPolyhedron(scene._scene, origins, normals, face_colors, N, r);
        self.material = material;
        self.outline_material = outline_material;
        self.outline_width = outline_width;
        self._radius = r;

        if position is not None:
            self.position[:] = position;

        if orientation is not None:
            self.orientation[:] = orientation;

        if color is not None:
            self.color[:] = color;

        self.scene = scene;
        self.scene.geometry.append(self);

    def get_extents(self):
        R""" Get the extents of the geometry

        Returns:
            [[minimum x, minimum y, minimum z],[maximum x, maximum y, maximum z]]
        """
        pos = self.position[:];
        r = self._radius;
        res = numpy.array([numpy.min(pos - r, axis=0),
                           numpy.max(pos + r, axis=0)])
        return res;

    @property
    def position(self):
        return util.array(self._geometry.getPositionBuffer(), geom=self)

    @property
    def orientation(self):
        return util.array(self._geometry.getOrientationBuffer(), geom=self)

    @property
    def color(self):
        return util.array(self._geometry.getColorBuffer(), geom=self)

    @property
    def color_by_face(self):
        return self._geometry.getColorByFace();

    @color_by_face.setter
    def color_by_face(self, v):
        self._geometry.setColorByFace(v);
