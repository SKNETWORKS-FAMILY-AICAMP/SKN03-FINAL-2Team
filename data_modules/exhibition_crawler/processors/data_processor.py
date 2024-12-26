import openai
import easyocr
import logging
import re
import warnings
from ..utils.paramstore import ParameterStore

warnings.filterwarnings(action='ignore')

class OCRProcessor:
    def __init__(self):
        self.reader = easyocr.Reader(['en', 'ko'])
        self.results = {}

    def process_exhibition_images(self, image_processor):
        for name, segments in image_processor.processed_images.items():
            logging.info(f"\n{name} OCR 처리 중...")
            
            try:
                results = self._process_image_group(segments)
                
                json_results = {
                    'results': [{
                        'text': text_info['text'],
                        'confidence': float(text_info['confidence'])
                    } for text_info in results]
                }
                
                texts_only = {
                    'texts': [self._clean_text(text_info['text']) 
                             for text_info in results 
                             if self._clean_text(text_info['text']).strip()]
                }
                
                self.results[name] = {
                    'full_results': json_results,
                    'texts_only': texts_only
                }
                
                logging.info(f"OCR 처리 완료: {name}")
                
            except Exception as e:
                logging.error(f"OCR 처리 중 오류 발생: {str(e)}")
                continue

    def _process_image_group(self, segments):
        seen_texts = {}
        
        for image in segments:
            if image is None:
                continue
                
            results = self.reader.readtext(
                image,
                paragraph=False,
                contrast_ths=0.1,
                text_threshold=0.5,
                low_text=0.3,
                width_ths=0.5,
                height_ths=0.5,
                add_margin=0.1,
            )
            
            for (bbox, text, confidence) in results:
                cleaned_text = self._clean_text(text)
                if cleaned_text.strip():
                    if cleaned_text not in seen_texts or confidence > seen_texts[cleaned_text]['confidence']:
                        seen_texts[cleaned_text] = {
                            'text': text,
                            'confidence': confidence,
                            'bbox': bbox
                        }
        
        return list(seen_texts.values())

    def _clean_text(self, text):
        text = re.sub(r'[^\w\s가-힣]', '', text)
        return ' '.join(text.split())

class PromptProcessor:
    def __init__(self):
        api_key = ParameterStore.get_parameter('OPENAI_API_KEY')

        if not api_key:
            raise ValueError("API 키가 설정되지 않았습니다. ParameterStore를 확인하세요.")
            
        self.client = openai.OpenAI()

    def process_ocr_results(self, ocr_texts):
        prompt = '''1. **Step 1: Define the Input**  
            {question}에 포함된 전시회의 정보를 읽고 이를 분석합니다. 전시회의 주제, 독특한 경험, 할인 혜택, 방문객 안내 정보를 추출하는 데 초점을 맞춥니다.
            2. **Step 2: Extract Key Themes and Purpose**  
            전시회의 주요 주제와 목적을 도출하세요. 이 전시회가 전달하려는 메시지와 감정을 명확히 정의하고, 이를 뒷받침하는 부가적인 테마와 서브스토리를 분석합니다.
            3. **Step 3: Highlight Unique Features and Experiences**  
            전시회의 독창적인 특징과 경험 요소를 기술합니다. 몰입형 경험, 기술 혁신, 상호작용 요소, 주목할 만한 작품을 포함하여 관람객에게 제공되는 주요 경험을 설명하세요.
            4. **Step 4: Summarize Discount Benefits and Events**  
            할인 혜택과 프로모션 정보, 특별 이벤트를 요약하세요. 할인 조건, 적용 대상, 기간, 독점 이벤트 내용을 포함하여 전시회의 매력을 극대화할 수 있는 요소를 추가합니다.
            5. **Step 5: Provide Practical Visitor Guidance**  
            티켓 구매 방법, 사용 조건, 입장 규정, 전시장 위치, 운영 시간, 추가 정보(주차, 어린이 정책 등)를 상세히 정리하세요.
            6. **Step 6: Combine Information into a Single Sentence**  
            앞서 추출된 모든 정보를 하나의 문장으로 통합하세요. 전시회의 주제, 특징, 할인 혜택, 방문 안내를 모두 포함하여 흐름이 자연스럽고 정보가 풍부한 문장을 작성합니다.
            7. **Step 7: Translate and Finalize in Korean**  
            최종 문장을 한국어로 번역하며, 자연스럽고 읽기 쉽게 조정하세요. , 최종 결과물만 한글로 출력하세요 또한 최소 300자 이상 출력하세요.
            '''

        try:
            response = self.client.chat.completions.create(
                model='gpt-4o-mini',
                messages=[
                    {"role": "user", "content": prompt + "\n" + "\n".join(ocr_texts)},
                ]
            )
            result = response.choices[0].message.content.strip()
            return result
        except Exception as e:
            logging.error(f"프롬프트 처리 중 오류 발생: {str(e)}")
            return None 