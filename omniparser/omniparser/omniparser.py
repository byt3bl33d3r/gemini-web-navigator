from omniparser.utils import get_som_labeled_img, check_ocr_box, get_caption_model_processor, get_yolo_model
from pprint import pprint
from PIL import Image
import io
import base64
from uuid import uuid4


class Omniparser:
    def __init__(self):
        self.box_threshold = 0.05
        self.yolo_model = get_yolo_model(model_path='weights/icon_detect_v1_5/model_v1_5.pt')
        self.caption_model_processor = get_caption_model_processor(model_name="florence2", model_name_or_path="weights/icon_caption_florence")

    def parse(self, image_input: str, use_paddleocr: bool = True, iou_threshold: float = 0.1, imgsz: int = 640):
        image_save_path = f"imgs/{uuid4()}.png"
        image_input.save(image_save_path)

        print('Parsing image:', image_save_path)
        image = Image.open(image_save_path)

        box_overlay_ratio = image.size[0] / 3200
        draw_bbox_config = {
            'text_scale': 0.8 * box_overlay_ratio,
            'text_thickness': max(int(2 * box_overlay_ratio), 1),
            'text_padding': max(int(3 * box_overlay_ratio), 1),
            'thickness': max(int(3 * box_overlay_ratio), 1),
        }

        ocr_bbox_rslt, is_goal_filtered = check_ocr_box(
            image_save_path, display_img = False, output_bb_format='xyxy', goal_filtering=None
            #easyocr_args={'paragraph': False, 'text_threshold':0.9}, use_paddleocr=use_paddleocr
        )
        text, ocr_bbox = ocr_bbox_rslt

        dino_labled_img, label_coordinates, parsed_content_list = get_som_labeled_img(
            image_save_path, self.yolo_model, BOX_TRESHOLD = self.box_threshold, output_coord_in_ratio=True, 
            ocr_bbox=ocr_bbox,draw_bbox_config=draw_bbox_config, caption_model_processor=self.caption_model_processor, 
            ocr_text=text, iou_threshold=iou_threshold, imgsz=imgsz
        )

        image = Image.open(io.BytesIO(base64.b64decode(dino_labled_img)))
        print('finish processing')
        return image, parsed_content_list, label_coordinates


if __name__ == "__main__":
    parser = Omniparser()

    #  time the parser
    import time
    s = time.time()
    image, parsed_content_list, label_coordinates = parser.parse(
        Image.open('../Omniparser/imgs/saved_image_demo.png')   
    )

    image.save('test.png')
    pprint(parsed_content_list)
    pprint(label_coordinates)

    print(f"Time taken for Omniparser: {time.time() - s}")
