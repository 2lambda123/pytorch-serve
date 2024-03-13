from torchvision.models.resnet import Bottleneck, ResNet


class ResNet152ImageClassifier(ResNet):
    def __init__(self):
        super(ResNet152ImageClassifier, self).__init__(Bottleneck, [3, 8, 36, 3])
