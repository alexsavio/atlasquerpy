import nipy
import nibabel as nib
from nipy.io.nifti_ref import nifti2nipy
from nipy.core.reference.array_coords import ArrayCoordMap

def voxcoord_to_mm(cm, i, j, k):
    '''
    Parameters
    ----------
    cm: nipy.core.reference.coordinate_map.CoordinateMap

    x, y, z: floats

    Returns
    -------
    Triplet with real 3D world coordinates

    '''
    try:
        mm = cm([i, j, k])
    except:
        print('coord_transform.voxcoord_to_mm error on converting coordinates')
        raise

    return mm


def mm_to_voxcoord(cm, x, y, z):
    '''
    Parameters
    ----------
    cm: nipy.core.reference.coordinate_map.CoordinateMap

    x, y, z: floats

    Returns
    -------
    Triplet with 3D voxel coordinates
    '''
    try:
        vox = cm.inverse()([x, y, z])
    except:
        print('coord_transform.mm_to_voxcoord error on converting coordinates')
        raise

    return vox


def get_3D_coordmap(img):
    '''
    Gets a 3D CoordinateMap from img.

    Parameters
    ----------
    img: nib.Nifti1Image or nipy Image

    Returns
    -------
    nipy.core.reference.coordinate_map.CoordinateMap
    '''
    if isinstance(img, nib.Nifti1Image):
        img = nifti2nipy(img)

    if img.ndim == 4:
        from nipy.core.reference.coordinate_map import drop_io_dim
        cm = drop_io_dim(img.coordmap, 3)
    else:
        cm = img.coordmap

    return cm


def get_coordmap_array(coordmap, shape):
    '''
    See: http://nipy.org/nipy/stable/api/generated/nipy.core.reference.array_coords.html?highlight=grid#nipy.core.reference.array_coords.Grid
    '''
    return ArrayCoordMap(coordmap, shape)




