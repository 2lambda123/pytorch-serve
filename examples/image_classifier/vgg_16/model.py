from torchvision.models.vgg import VGG, cfgs, make_layers


class ImageClassifier(VGG):
    def __init__(self):
        super(ImageClassifier, self).__init__(
            make_layers(cfgs["D"], False), **{"init_weights": False}
        )
