import os

class AutoCADRasterTool:
    def __init__(self, acad):
        self.acad = acad

    def insert_image(self, image_path):
        command = f"IINSERT {image_path}\n"
        self.acad.ActiveDocument.SendCommand(command)

    def recognize_raster(self):
        command = "IRECOGNIZE\n"
        self.acad.ActiveDocument.SendCommand(command)

    def save_file(self, file_path):
        command = f"SAVEAS {file_path}\n"
        self.acad.ActiveDocument.SendCommand(command)

    def process_batch(self, image_list, output_dir):
        for image_path in image_list:
            self.insert_image(image_path)
            self.recognize_raster()
            output_file = f"{output_dir}/{os.path.basename(image_path)}_clean.dwg"
            self.save_file(output_file)
