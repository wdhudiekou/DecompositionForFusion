from torch.utils.data import Dataset
import os
import json
import torch
import torchvision.transforms.functional as TF
from torchvision.transforms import Compose, RandomResizedCrop, ToTensor
import torch.nn.functional as F
import cv2
from tqdm import tqdm
from PIL import Image


class TrainDataset(Dataset):
    def __init__(self, trainopt):
        super(TrainDataset, self).__init__()
        path = trainopt['dataroot']
        self.img_transform = ToTensor()
        self.img_resize = RandomResizedCrop(trainopt['image_size'])
        self.image_size = trainopt['image_size']
        self.batch_size = trainopt['iter_size']
        self.max_iter = trainopt["max_iter"]
        self.epoch_num = 0

        trainpairs_forreading = str(trainopt['trainpairs'])
        if not os.path.exists(trainpairs_forreading):
            self.iget_imgs = {}
            part1_imgs = os.path.join(os.path.expanduser(path), trainopt["part1_name"])
            part2_imgs = os.path.join(os.path.expanduser(path), trainopt["part2_name"])

            def not_dir(x):
                return 'Label' not in x and '.json' not in x and '.DS_Store' not in x
            part1_imgs = [os.path.join(part1_imgs, os_dir) for os_dir in filter(not_dir, os.listdir(part1_imgs)) ]
            part2_imgs = [os.path.join(part2_imgs, os_dir) for os_dir in filter(not_dir, os.listdir(part2_imgs)) ]

            over_imgs = []
            under_imgs = []
            for img_seq in tqdm(part1_imgs + part2_imgs):
                ov_seq = {}
                for img_name in filter(not_dir, os.listdir(img_seq)):
                    img = cv2.imread(os.path.join(img_seq, img_name), 1)
                    ov_seq[img_name] = img.mean()
                over_imgs.append(os.path.join(img_seq, max(ov_seq, key=ov_seq.get)))
                under_imgs.append(os.path.join(img_seq, min(ov_seq, key=ov_seq.get)))

            over_imgs.sort()
            under_imgs.sort()

            self.iget_imgs = {}
            for o_img, u_img in zip(over_imgs, under_imgs):
                self.iget_imgs[str(o_img)] = [o_img, u_img]

            with open(trainpairs_forreading, 'w') as f:
                json.dump(self.iget_imgs, f)
        else:
            with open(trainpairs_forreading, 'r') as f:
                self.iget_imgs = json.load(f)
        self.iget_imgs = [(key, values) for key, values in self.iget_imgs.items()]
        self.iget_imgs = sorted(self.iget_imgs, key=lambda x: x[0])

    def __len__(self):
        return len(self.iget_imgs)

    def __getitem__(self, index):
        c_img, (o_img, u_img) = self.iget_imgs[index]
        # print(c_img, o_img, u_img)
        # o_img = cv2.imread(o_img, 1)
        # u_img = cv2.imread(u_img, 1)

        o_img = Image.open(o_img).convert("RGB")
        u_img = Image.open(u_img).convert("RGB")

        o_img = self.img_transform(o_img)
        u_img = self.img_transform(u_img)
        # print("size", o_img.shape, u_img.shape)
        combime_img = self.img_resize(torch.cat((o_img, u_img), dim=0))
        o_img = combime_img[:3, :, :]
        u_img = combime_img[3:, :, :]

        return o_img, u_img, _
