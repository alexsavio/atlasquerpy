import nipy
import nibabel as nib

def is_valid_coordinate(img, i, j, k):
    '''
    '''
    imgX, imgY, imgZ = img.shape
    return ((i >= 0 and i < imgX) and
            (j >= 0 and j < imgY) and
            (k >= 0 and k < imgZ))


def are_compatible_imgs(one_img, another_img):
    '''
    Returns true if one_img and another_img have the same shape, false
    otherwise.
    '''
    return (one_img.shape == another_img.shape)

