
import os
import nibabel as nib
from atlas import Atlas, StatsAtlas, LabelAtlas


class AtlasFiles:


    def __init__(self):
        '''
        '''
        self.fsl_dir = ''
        self.mni = ''
        self.atlas_path = ''


    def get_FSL_dir(self):
        '''
        '''
        if not self.fsl_dir:
            self.fsl_dir = '/usr/share/fsl'
            if os.environ.has_key('FSLDIR') and os.environ['FSLDIR'] != '':
                self.fsl_dir = os.environ['FSLDIR']
            else:
                print('Could not obtain $FSLDIR environment variable value.')

        return self.fsl_dir


    def get_mni152(self):
        '''
        '''
        if not self.mni:
            self.mni = os.path.join(self.get_FSL_dir(),
                                    'data',
                                    'standard',
                                    'MNI152_T1_2mm_brain.nii.gz')

        return self.mni


    def get_atlas_path(self):
        '''
        '''
        if not self.atlas_path:
            if os.environ.has_key('FSLATLASPATH'):
                self.atlas_path = os.environ['FSLATLASPATH']
            else:
                self.atlas_path = os.path.join(self.get_FSL_dir(), 
                                               'data', 
                                               'atlases')

        return self.atlas_path


    def get_atlas_path_elements(self):
        '''
        '''
        dir_path = self.get_atlas_path()

        return dir_path.split(':')


    def find(self, lst, regex):
        '''
        Looks for string matches of regex in lst.

        Parameters
        ----------
        lst: list of strings

        regex: string
        Pythonic regular expression to be matched

        Returns
        -------
        List of strings 

        '''
        import re

        o = []
        for i in lst:
            if re.search(regex, i):
                o.append(i)
        return o


    def read_image(self, atlas_dir, images_node, tag):
        '''
        Looks for an Element node between images_node children with name tag.
        This element will hold a relative path to an atlas volume file, which
        will be opened and returned as nib.Nifti1Image.

        Parameters
        ----------
        atlas_dir: string

        images_node: xml dom node

        tag: string

        Returns
        -------
        nib.Nifti1Image
        '''
        for node in images_node.childNodes:
            if node.nodeType == node.ELEMENT_NODE and node.nodeName == tag:
                node_text = str(node.firstChild.data)
                if node_text:
                    full_atlas_dir = os.path.join(atlas_dir, os.path.dirname(node_text)[1:])

                    file_base_name = os.path.basename(node_text)

                    full_file = self.find(os.listdir(full_atlas_dir), file_base_name)[0]

                    img = nib.load(os.path.join(full_atlas_dir, full_file))

        return img


    def _get_dom_attribute_value(self,node, att_name, alt=''):
        '''
        '''
        if node.attributes.has_key(att_name):
            return node.attributes[att_name].value
        else:
            return alt


    def read_xml_atlas(self, atlas_dir, file_name):
        '''
        Process the data inside an Atlas definition XML file and returns the 
        corresponding Atlas.

        Parameters
        ----------
        atlas_dir: string

        file_name: string

        Returns
        -------
        Atlas

        '''
        from xml.dom import minidom

        full_path = os.path.join(atlas_dir, file_name)

        try:
            dom = minidom.parse(full_path)
        except IOError:
            print ("Error: can\'t find file or read " + full_path)
            
            raise

        root = dom.documentElement

        atlas_name = ''
        atlas_type = None
        atlas_images = []
        atlas_summaries = []
        lower = -100
        upper = 100
        precision = 0
        stats_name = ''
        units = ''

        for node in root.childNodes:

            if node.nodeType == node.ELEMENT_NODE:
                node_name = node.nodeName
                if node_name == 'header':
                    for curr_node in node.childNodes:

                        if curr_node.nodeType == node.ELEMENT_NODE:
                            curr_node_name = curr_node.nodeName

                            if curr_node_name == 'name':
                                node_text = str(curr_node.firstChild.data)
                                if node_text:
                                    atlas_name = node_text

                            elif curr_node_name == 'units':
                                node_text = str(curr_node.firstChild.data)
                                if node_text:
                                    units = node_text

                            elif curr_node_name == 'precision':
                                node_text = str(curr_node.firstChild.data)
                                if node_text:
                                    precision = int(node_text)

                            elif curr_node_name == 'upper':
                                node_text = str(curr_node.firstChild.data)
                                if node_text:
                                    upper = float(node_text)

                            elif curr_node_name == 'lower':
                                node_text = str(curr_node.firstChild.data)
                                if node_text:
                                    lower = float(node_text)

                            elif curr_node_name == 'statistic':
                                node_text = str(curr_node.firstChild.data)
                                if node_text:
                                    stats_name = node_text

                            elif curr_node_name == 'type':
                                node_text = str(curr_node.firstChild.data)
                                if node_text:
                                    if node_text.lower() == 'label':
                                        atlas_type = 'label'
                                    elif node_text.lower() == 'probabilistic':
                                        atlas_type = 'probs'
                                        units = '%'
                                        lower = 0
                                        upper = 100
                                        precision = 0

                                    else:
                                        atlas_type = 'probs'

                            elif curr_node_name == 'images':
                                atlas_images.append(self.read_image(atlas_dir,
                                                                    curr_node,
                                                                    'imagefile'))

                                atlas_summaries.append(self.read_image(atlas_dir,
                                                                       curr_node,
                                                                       'summaryimagefile'))

        if atlas_type == 'probs':
            atlas = StatsAtlas(atlas_images, atlas_summaries, atlas_name,
                               lower, upper, precision, stats_name, units)

        elif atlas_type == 'label':
            atlas = LabelAtlas(atlas_images, atlas_summaries, atlas_name)


        for node in root.childNodes:
            node_name = node.nodeName
            if node.nodeType == node.ELEMENT_NODE and node_name == 'data':
                for curr_node in node.childNodes:

                    if curr_node.nodeType == node.ELEMENT_NODE:
                        curr_node_name = curr_node.nodeName
                        if curr_node_name == 'label':
                            n = int(self._get_dom_attribute_value(curr_node, 
                                                                  'index', '0'))
                            l = str(curr_node.firstChild.data)
                            atlas.add_label(n, l)

                            x = int(self._get_dom_attribute_value(curr_node, 'x', '0'))
                            y = int(self._get_dom_attribute_value(curr_node, 'y', '0'))
                            z = int(self._get_dom_attribute_value(curr_node, 'z', '0'))
                            v = int(self._get_dom_attribute_value(curr_node, 'v', '0'))

                            #ref = self._get_dom_attribute_value(curr_node, 'ref', '')

                            atlas.add_centre(n, x, y, z, v)
                            #atlas.add_reference(n, ref)

        return atlas


