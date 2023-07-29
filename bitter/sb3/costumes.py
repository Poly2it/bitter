from PIL import Image

from io import BytesIO

import rich.repr

from hashlib import md5

class Costume:
    def __init__(self, name: str, extension: str, data: bytes):
        self.name: str = name
        self.data_format: str = extension
        self.asset_id: str = md5(data).hexdigest()
        self.md5_ext: str = f"{self.asset_id}.{self.data_format}"
        self.rotation_center_x: int = 0
        self.rotation_center_y: int = 0

        self.data = data

class Vector(Costume):
    def __init__(self, name: str, extension: str, data: bytes):
        super().__init__(name, extension, data)
        
    def render(self, file_buffer):
        file_buffer.update({self.md5_ext: self.data})

        return {
            "name": self.name,
            "dataFormat": self.data_format,
            "assetId": self.asset_id,
            "md5ext": self.md5_ext,
            "rotationCenterX": self.rotation_center_x,
            "rotationCenterY": self.rotation_center_y
        }
    
    def __rich_repr__(self) -> rich.repr.Result:
        yield "name", self.name
        yield "data_format", self.data_format
        yield "asset_id", self.asset_id
        yield "md5_ext", self.md5_ext
        yield "rotation_center_x", self.rotation_center_x
        yield "rotation_center_y", self.rotation_center_y

class Bitmap(Costume):
    def __init__(self, name: str, extension: str, data: bytes, size):
        super().__init__(name, extension, data)
        self.bitmap_resolution = 2
        self.rotation_center_x = size[0]
        self.rotation_center_y = size[1]

    def render(self, file_buffer):
        file_buffer.update({self.md5_ext: self.data})

        return {
            "name": self.name,
            "bitmapResolution": self.bitmap_resolution,
            "dataFormat": self.data_format,
            "assetId": self.asset_id,
            "md5ext": self.md5_ext,
            "rotationCenterX": self.rotation_center_x,
            "rotationCenterY": self.rotation_center_y
        }

def cast_to_costume(file, working_directory):
    file_type = file.suffix[1:]
    file_name = file.stem
    file_path = working_directory / file
        
    match file_type:
        case 'svg':
            with open(file_path, 'rb') as file:
                file_bytes = file.read()

            costume = Vector(file_name, file_type, file_bytes)

        case 'jpeg' | 'jpg' | 'png' | 'qoi':
            format_alias = {
                "jpeg": 'JPEG',
                "jpg": "JPEG",
                "png": "PNG",
                "qoi": "PNG"
            }
            
            with Image.open(file_path) as img:
                unscaled_size = img.size
                img = img.resize((unscaled_size[0] * 2, unscaled_size[1] * 2), resample=Image.Resampling.NEAREST)
                
                output_buffer = BytesIO()
                img.save(output_buffer, format_alias[file_type], optimize=True)

            costume = Bitmap(file_name, file_type, output_buffer.getvalue(), unscaled_size)

        case _:
            #TODO: supply proper error message
            print(f"{repr(file_type)} is not a valid costume file type")
            exit(1)

    return costume