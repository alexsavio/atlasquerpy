atlasquerpy
===========

FSL atlasquery in Python

This is a Python version of the FMRIB software library (FSL) atlasquery tool.

About FSL atlasquery
--------------------

It is widely used for post-hosc observations of brain analyses results. 
Using the atlases supplied with the FSL tools, it makes queries to atlas images
from the command-line.

Motivation
----------
I programmed this to be able to easily modify its code.
I could modify the original C++ atlasquery, but compiling it can be a pain in
the ass as it uses versions of Qt, Qwt and VTK libraries which are not the same
as in my Ubuntu configuration.


Atlasquerpy is slower than atlasquery. It depends on the number of voxels in the
mask, where the original atlasquery depended mostly on the resolution of it.

Dependencies
------------
Atlasquerpy makes use of some Python libraries:
Numpy
NiBabel
Nipy
XML
argparse

References
----------
http://fsl.fmrib.ox.ac.uk/fsl/fslwiki/Atlasquery
