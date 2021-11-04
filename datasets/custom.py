from torch.utils.data import Dataset
from datasets.data_io import read_cam_file, read_pair_file, read_image
import os
import numpy as np
import cv2


class MVSDataset(Dataset):
    def __init__(self, datapath, n_views=3, img_wh=(736, 416)):
        
        self.stages = 4
        self.datapath = datapath
        self.img_wh = img_wh
        
        self.metas = read_pair_file(os.path.join(self.datapath, 'pair.txt'))
        self.n_views = n_views
        
    def __len__(self):
        return len(self.metas)

    def __getitem__(self, idx):
        
        ref_view, src_views = self.metas[idx]
        # use only the reference view and first nviews-1 source views
        view_ids = [ref_view] + src_views[:self.n_views-1]

        imgs_0 = []
        imgs_1 = []
        imgs_2 = []
        imgs_3 = []
        
        # depth = None
        depth_min = None
        depth_max = None
        
        proj_matrices_0 = []
        proj_matrices_1 = []
        proj_matrices_2 = []
        proj_matrices_3 = []

        for i, vid in enumerate(view_ids):
            img_filename = os.path.join(self.datapath, f'images/{vid:08d}.jpg')
            proj_mat_filename = os.path.join(self.datapath, f'cams/{vid:08d}_cam.txt')

            # image, original_h, original_w = read_image(img_filename, max(self.img_wh))
            image, original_h, original_w = read_image(img_filename, self.img_wh)
            imgs_0.append(image)
            imgs_1.append(cv2.resize(image, (self.img_wh[0]//2, self.img_wh[1]//2), interpolation=cv2.INTER_LINEAR))
            imgs_2.append(cv2.resize(image, (self.img_wh[0]//4, self.img_wh[1]//4), interpolation=cv2.INTER_LINEAR))
            imgs_3.append(cv2.resize(image, (self.img_wh[0]//8, self.img_wh[1]//8), interpolation=cv2.INTER_LINEAR))

            intrinsics, extrinsics, depth_params = read_cam_file(proj_mat_filename)
            intrinsics[0] *= self.img_wh[0]/original_w
            intrinsics[1] *= self.img_wh[1]/original_h

            proj_mat = extrinsics.copy()
            intrinsics[:2, :] *= 0.125
            proj_mat[:3, :4] = np.matmul(intrinsics, proj_mat[:3, :4])
            proj_matrices_3.append(proj_mat)

            proj_mat = extrinsics.copy()
            intrinsics[:2, :] *= 2
            proj_mat[:3, :4] = np.matmul(intrinsics, proj_mat[:3, :4])
            proj_matrices_2.append(proj_mat)

            proj_mat = extrinsics.copy()
            intrinsics[:2, :] *= 2
            proj_mat[:3, :4] = np.matmul(intrinsics, proj_mat[:3, :4])
            proj_matrices_1.append(proj_mat)

            proj_mat = extrinsics.copy()
            intrinsics[:2, :] *= 2
            proj_mat[:3, :4] = np.matmul(intrinsics, proj_mat[:3, :4])
            proj_matrices_0.append(proj_mat)

            if i == 0:  # reference view
                depth_min = depth_params[0]
                depth_max = depth_params[1]

        # imgs: N*3*H0*W0, N is number of images
        imgs = {
            'stage_0': np.stack(imgs_0).transpose([0, 3, 1, 2]),
            'stage_1': np.stack(imgs_1).transpose([0, 3, 1, 2]),
            'stage_2': np.stack(imgs_2).transpose([0, 3, 1, 2]),
            'stage_3': np.stack(imgs_3).transpose([0, 3, 1, 2])
        }
        # proj_matrices: N*4*4
        proj = {
            'stage_3': np.stack(proj_matrices_3),
            'stage_2': np.stack(proj_matrices_2),
            'stage_1': np.stack(proj_matrices_1),
            'stage_0': np.stack(proj_matrices_0)
        }

        return {"imgs": imgs,                   # N*3*H0*W0
                "proj_matrices": proj,          # N*4*4
                "depth_min": depth_min,         # scalar
                "depth_max": depth_max,         # scalar
                "filename": '{}/' + '{:0>8}'.format(view_ids[0]) + "{}"
                }
