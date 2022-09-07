
import pathlib
import numpy as np
import matplotlib.pyplot as plt

import cv2
import torch
from torchvision import models, transforms
from copy import deepcopy


# prepare transformer
prepare = transforms.Compose([
    transforms.ToTensor(),
    transforms.Resize((224, 224)),
    transforms.Normalize(mean=[0.485, 0.456, 0.406],
                         std=[0.229, 0.224, 0.225]),
])

augment = transforms.Compose([
    # transforms.ColorJitter(brightness=1.25),
    # transforms.GaussianBlur(3),
# try add something here
])


class GestData(torch.utils.data.Dataset):
    def __init__(self, root, *, fmask='*/*', transform=None, augment=None, seed=None):
        # initialize randomizer
        self.randomizer = np.random.default_rng(seed)
        self.root = pathlib.Path(root)
        self.transform = transform
        self.augment = augment
        # collect files
        self.collection = np.array(list(pathlib.Path('data').glob(fmask)))
        # collect classes dict
        self.classes = list(set([f.parts[-2] for f in self.collection]))
        self.decode_class = dict(enumerate(self.classes))
        self.encode_class = {v: k for k, v in self.decode_class.items()}
        # generate collection
        self.randomizer.shuffle(self.collection)
        self.labels = np.array([f.parts[-2] for f in self.collection])
    
    def __getitem__(self, index):
        file = self.collection[index]
        label = self.labels[index]
        # read image
        image = cv2.cvtColor(cv2.imread(file.as_posix()), cv2.COLOR_BGR2RGB)
            
        # preprocess
        if self.transform is not None:
            image = self.transform(image)
        # augmentations
        if self.augment is not None:
            image = self.augment(image)
        return image, self.encode_class[label]

    def __len__(self):
        return len(self.collection)
    
    def partition(self, arange):
        part = deepcopy(self)
        part.collection = part.collection[arange]
        part.labels = part.labels[arange]
        return part

    def overview(self, index=None, **kwargs):
        index = index if index else np.random.default_rng().integers(len(self.collection))
        image, clabel = self[index]
        plt.title(f'index: {index}; label: {self.decode_class[clabel]}; class: {clabel}')
        plt.imshow(image.permute(1, 2, 0))
        plt.show()



# model arch
class GestPretrained(torch.nn.Module):
    def __init__(self, output_dim, *, N=2):
        super().__init__()
        self.model = models.resnet50(weights=models.ResNet50_Weights.DEFAULT)
        self.model.fc = torch.nn.Linear(2048, output_dim)

        param_names = [name for name, _ in self.model.named_parameters()]
        assert N <= len(param_names), f"N must be <= length of pretrained network parameters count"
        self.params_to_update = []
        for name, param in self.model.named_parameters():
            if name in param_names[:-N]:
                param.requires_grad = False
            else:
                self.params_to_update.append(param)
    
    def forward(self, x):
        out = self.model(x)
        return torch.softmax(out, dim=1)
