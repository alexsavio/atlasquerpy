#!/usr/bin/python

import numpy as np
from nipy.io.nifti_ref import nifti2nipy

from coord_transform import voxcoord_to_mm, mm_to_voxcoord
from coord_transform import get_3D_coordmap, get_coordmap_array
from image_info import is_valid_coordinate, are_compatible_imgs

class Atlas:
    '''
    Stores atlases data
    '''

    def __init__(self, imgs, summs, name): 
        '''
        Parameters
        ----------
        imgs: list of nib.Nifti1Image
        Volumes

        summs: list of nib.Nifti1Image
        Summary images

        name: string
        Atlas name
        '''
        self.name = name
        self.images = imgs
        self.summaries = summs

        self.labels = {}
        self.references = {}

        self.cursors = {}

        self.image = self.images[0]
        self.summary = self.summaries[0]

        self.type = ''


    def get_volume(self, pos):
        '''
        Parameters
        ----------
        pos: int
        Position of the volume in the images array

        Returns
        -------
        nib.Nifti1Image
        '''
        return self.images[pos] if self.images.has_key(pos) else None


    def find_label(self, pos):
        '''
        Returns the label string corresponding to pos
        Parameters
        ----------
        pos: int
        Position of the label in the labels array

        Returns
        -------
        string
        '''
        return self.labels[pos] if self.labels.has_key(pos) else None


    def add_label(self, n, name):
        '''
        Parameters
        ----------
        pos: int
        Position of the label in the labels array

        Returns
        -------
        a tuple: (label_value, string)
        '''
        self.labels[n] = name


    def get_labels_ids(self):
        '''
        '''
        return self.labels.keys()


    def get_num_labels(self):
        '''
        Returns number of labels in the atlas
        '''
        return len(self.labels)


    def select_compatible_images(self, ref_img):
        '''
        Sets self.image and self.summary to images compatible with ref_image

        Parameters
        ----------
        ref_img: nib.Nifti1Image or Nipy Image
        '''
        for atlas_img in self.images:
            if are_compatible_imgs(atlas_img, ref_img):
                self.image = atlas_img

        for atlas_summ in self.summaries:
            if are_compatible_imgs(atlas_summ, ref_img):
                self.summary = atlas_summ


    def get_structure_name(self, index):
        '''
        '''
        return self.labels[index] if self.labels.has_key(index) else 'Unknown'


    def add_centre(self, n, x, y, z, v):
        '''
        '''
        self.cursors[n] = (x, y, z, v)



class StatsAtlas (Atlas):
    '''
    Stores statistical atlases data
    '''
    def __init__(self, imgs, summs, name, lower, upper, precision, 
                 stats_name, units): 
        '''
        imgs: list of nib.Nifti1Image
        summs: list of nib.Nifti1Image
        name: string
        Atlas name
        '''
        Atlas.__init__(self, imgs, summs, name)

        self.lower = lower
        self.upper = upper
        self.precision = precision
        self.stats_name = stats_name
        self.units = units

        self.type = 'stat'


    def get_probability(self, struct_idx, x, y, z):
        '''
        Returns the probability value of coordinate x,y,z in mm given the
        structure.
        If the structure does not exist or the coordinate is not valid, will
        return 0.

        Parameters
        ----------
        struct_idx: int
        Index of the atlas' structure of interest.

        x, y, z: float
        Spatial coordinates of the point of interest

        Returns
        -------
        a float value of the probability

        '''
        i, j, k = mm_to_voxcoord(self.image, x, y, z)

        if self.image.shape[3] <= struct_idx:
            return 0

        if is_valid_coordinate(self.image, i, j, k):
            return self.image.get_data()[i, j, k, struct_idx]
        else:
            return 0


    def _get_roi_mask_intersect(self, mask_img, struct_idx):
        '''
        Parameters
        ----------
        mask_img: nib.Nifti1Image or nipy Image

        struct_idx: int

        Returns
        -------
        The total sum of 

        '''
        mask_vol = np.array(mask_img.get_data())

        if self.image.shape[3] <= struct_idx:
            return 0

        prob_img = nifti2nipy(self.image)
        prob_vol = prob_img[:, :, :, struct_idx]

        masked_probs = 0.0

        mask_cm = get_3D_coordmap(mask_img)
        prob_cm = get_3D_coordmap(prob_img)

        for idx in np.argwhere(mask_vol):
            voxc = mm_to_voxcoord(prob_cm, *voxcoord_to_mm(mask_cm, *idx))
            masked_probs += prob_vol[tuple(voxc)] * mask_vol[tuple(idx)]

        return masked_probs


    def get_avg_probability(self, mask_img, struct_idx):
        '''
        Calculates the average probability of the atlas voxels that belong to
        mask_img.

        Parameters
        ----------
        mask_img: nib.Nifti1Image

        struct_idx: int
        Index of the atlas' structure of interest.

        Returns
        -------
        float number of the resulting average probability
        '''
        mask_img = nifti2nipy(mask_img)
        mask_vol = mask_img.get_data()

        if self.image.shape[3] <= struct_idx:
            return 0

        prob_img = nifti2nipy(self.image)
        prob_vol = prob_img[:, :, :, struct_idx]

        total = 0.
        mask_sum = np.sum(mask_vol)

        masked_probs = self._get_roi_mask_intersect(mask_img, struct_idx)

        return masked_probs/mask_sum if mask_sum > 0 else 0


    def get_roi_overlap(self, mask_img, struct_idx, bin_prob=False):
        '''
        Calculates the percentage overlap of mask_img and the ROI given by
        struct_idx

        Parameters
        ----------
        mask_img: nib.Nifti1Image

        struct_idx: int
        Index of the atlas' structure of interest.

        bin_prob: boolean
        True if it is to binarise ROI probability map, False otherwise

        Returns
        -------
        float number of the resulting ROI overlap percentage
        '''
        mask_img = nifti2nipy(mask_img)
        mask_vol = mask_img.get_data()

        if self.image.shape[3] <= struct_idx:
            return 0

        prob_vol = self.image.get_data()[:, :, :, struct_idx]

        if bin_prob:
            prob_sum = np.sum(prob_vol>0)
        else:
            prob_sum = np.sum(prob_vol)

        masked_probs = self._get_roi_mask_intersect(mask_img, struct_idx)

        return masked_probs/prob_sum if prob_sum > 0 else 0


    def get_description(self, x, y, z):
        '''
        Returns the label corresponding to the given coordinates
        Parameters
        ----------
        x, y, z: int
        Coordinates in mm of the point of interest.

        Returns
        -------
        string

        i, j, k = mm_to_voxcoord(self.image, x, y, z)

        if is_valid_coordinate(self.image, i, j, k):
            index = self.image.get_data()[i, j, k]
        else:
            index = 0

        text = self.name
        if self.labels.has_key(index):
            text += ': ' + self.labels[index]

        return text
        '''
        i, j, k = mm_to_voxcoord(self.image, x, y, z)

        precision = 10**self.precision
        n_vols = self.image.shape[3]

        labels = {}
        for v in xrange(n_vols):
            vol = self.image.get_data()[:, :, :, v]

            try:
                stat = vol[i, j, k]
            except:
                stat = 0

            if round(stat * precision) != 0:
                if self.find_label(v) is not None:
                    labels.append((stat, self.find_label(v)))

        count = 0
        text = self.name + '\n'

        for pair in labels:
            stat = pair[0]
            label = pair[1]

            if count:
                text += ', '

            text += str(round(stat, self.precision))

            if self.stats_name:
                text += self.stats_name + '='

            if self.units: 
                text += self.units

            text += ' ' + label

        if not count:
            text += 'No label found.'

        return text



class LabelAtlas (Atlas):
    '''
    Stores statistical atlases data
    '''
    def __init__(self, imgs, summs, name): 
        '''
        imgs: list of nib.Nifti1Image
        summs: list of nib.Nifti1Image
        name: string
        Atlas name
        '''
        Atlas.__init__(self, imgs, summs, name)

        self.type = 'label'


    def get_probability(self, structure, x, y, z):
        '''
        Parameters
        ----------
        structure: int
        Number of the structure in the atlas

        x, y, z: float
        Coordinate in milimeters

        Returns
        -------
        int: 100 if the coordinate corresponds to the given structure, 0 if not
        '''
        i, j, k = mm_to_voxcoord(self.img, x, y, z)

        vol = self.get_volume(0).get_data()

        return 100 if vol[i, j, k] == structure else 0


    def _get_roi_mask_intersect(self, mask_img, struct_idx):
        '''
        Parameters
        ----------
        mask_img: nib.Nifti1Image or nipy Image

        struct_idx: int

        Returns
        -------
        The total sum of 

        '''
        mask_vol = np.array(mask_img.get_data())

        if self.image.shape[3] <= struct_idx:
            return 0

        lab_img = nifti2nipy(self.image)
        lab_vol = lab_img[:, :, :, struct_idx]

        masked_probs = 0.0

        mask_cm = get_3D_coordmap(mask_img)
        lab_cm = get_3D_coordmap(lab_img)
        for idx in np.argwhere(mask_vol):
            voxc = mm_to_voxcoord(lab_cm, *voxcoord_to_mm(mask_cm, *idx))
            prob = 100 if lab_vol[tuple(voxc)] == struct_idx else 0
            masked_probs += prob * mask_vol[tuple(idx)]

        return masked_probs


    def get_avg_probability(self, mask_img, struct_idx):
        '''
        Calculates the average probability of the atlas voxels that belong to
        mask_img.

        Parameters
        ----------
        mask_img: nib.Nifti1Image

        struct_idx: int
        Index of the atlas' structure of interest.

        Returns
        -------
        float number of the resulting average probability
        '''
        mask_img = nifti2nipy(mask_img)
        mask_vol = mask_img.get_data()

        if self.image.shape[3] <= struct_idx:
            return 0

        lab_vol = self.image.get_data()

        mask_sum = np.sum(mask_vol)
        masked_probs = self._get_roi_mask_intersect(mask_img, struct_idx)

        return masked_probs/mask_sum if mask_sum > 0 else 0


    def get_roi_overlap(self, mask_img, struct_idx):
        '''
        Calculates the percentage overlap of mask_img and the ROI given by
        struct_idx

        Parameters
        ----------
        mask_img: nib.Nifti1Image

        struct_idx: int
        Index of the atlas' structure of interest.

        Returns
        -------
        float number of the resulting ROI overlap percentage
        '''
        mask_vol = mask_img.get_data()

        if self.image.shape[3] <= struct_idx:
            return 0

        lab_vol = self.image.get_data()
        lab_sum = np.sum(lab_vol == struct_idx)

        masked_probs = self._get_roi_mask_intersect(mask_img, struct_idx)
        masked_probs /= 100

        return masked_probs/lab_sum if lab_sum > 0 else 0


    def get_description(self, x, y, z):
        '''
        Returns the label corresponding to the given coordinates
        Parameters
        ----------
        x, y, z: int
        Coordinates in mm of the point of interest.

        Returns
        -------
        string
        '''
        i, j, k = mm_to_voxcoord(self.image, x, y, z)

        if is_valid_coordinate(self.image, i, j, k):
            index = self.image.get_data()[i, j, k]
        else:
            index = 0

        text = self.name + '\n'
        if self.labels.has_key(index):
            text += self.labels[index]

        return text



