from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import time
import json
import os
import requests
import cv2
import numpy as np
import math
import easyocr
import re
from dotenv import load_dotenv
import openai

def sanitize_filename(filename):
        filename = filename.replace('［', '').replace('］', '')
        filename = filename.replace('[', '').replace(']', '')
        filename = filename.replace('＆', 'and')
        filename = filename.replace('&', 'and')
        filename = filename.replace(':', '_')
        filename = filename.replace('/', '_')
        filename = filename.replace('|', '_')
        filename = ' '.join(filename.split())
        filename = filename.strip()
        
        return filename

class DriverManager:
    @staticmethod
    def create_driver():
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920x1080')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        
        driver = webdriver.Chrome(options=chrome_options)
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        return driver

class ImageProcessor:
    def __init__(self):
        self.temp_images = {}
        self.processed_images = {}

    @staticmethod
    def _sanitize_filename(filename):
        return sanitize_filename(filename)

    def save_image(self, img_url, name, img_number):
        try:
            save_dir = os.path.join(os.getcwd(), "exhibition_images")
            if not os.path.exists(save_dir):
                os.makedirs(save_dir)
            
            response = requests.get(img_url, stream=True)
            if response.status_code == 200:
                if name not in self.temp_images:
                    self.temp_images[name] = []
                self.temp_images[name].append(response.content)
                print(f"이미지 {img_number} 임시 저장 완료: {name}")
            else:
                print(f"이미지 다운로드 실패 (상태 코드: {response.status_code}): {img_url}")
        except Exception as img_error:
            print(f"이미지 다운로드 중 오류: {str(img_error)}")

    def combine_and_save_images(self, name):
        try:
            if name not in self.temp_images or not self.temp_images[name]:
                print(f"{name}의 저장된 이미지가 없습니다")
                return
            
            images = []
            max_width = 0
            total_height = 0
            
            for idx, img_data in enumerate(self.temp_images[name]):
                try:
                    nparr = np.frombuffer(img_data, np.uint8)
                    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                    if img is None:
                        continue
                    
                    if img.shape[1] > 1500:
                        scale = 1500 / img.shape[1]
                        new_width = 1500
                        new_height = int(img.shape[0] * scale)
                        img = cv2.resize(img, (new_width, new_height))
                    
                    processed_img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                    images.append(processed_img)
                    max_width = max(max_width, processed_img.shape[1])
                    total_height += processed_img.shape[0]
                except Exception as e:
                    print(f"이미지 {idx+1} 처리 중 오류: {str(e)}")
            
            if not images:
                return
            
            combined = np.zeros((total_height, max_width, 3), dtype=np.uint8)
            y_offset = 0
            for img in images:
                if len(img.shape) == 2:
                    img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
                h, w = img.shape[:2]
                x_offset = (max_width - w) // 2
                combined[y_offset:y_offset+h, x_offset:x_offset+w] = img
                y_offset += h
            
            segments = self._split_image_with_overlap(combined)
            self.processed_images[name] = segments
            
            del self.temp_images[name]
            
        except Exception as e:
            print(f"전체 처리 중 에러: {str(e)}")

    def _split_image_with_overlap(self, image, overlap_percent=20):
        height, width = image.shape[:2]
        aspect_ratio = height / width
        base_segment_height = width * 3
        
        if aspect_ratio > 5:
            num_vertical = math.ceil(height / base_segment_height)
        else:
            num_vertical = 1
        
        segment_height = height // num_vertical
        overlap_pixels = int(segment_height * overlap_percent / 100)
        segments = []
        
        for i in range(num_vertical):
            start_y = max(0, i * segment_height - overlap_pixels)
            end_y = min(height, (i + 1) * segment_height + overlap_pixels)
            segment = image[start_y:end_y, 0:width]
            segments.append(segment)
        
        return segments

class ExhibitionDataCollector:
    def __init__(self, driver, image_processor):
        self.driver = driver
        self.image_processor = image_processor
        self.processed_items = set()
        self.exhibition_data = []

    def collect_exhibition_details(self, product, count):
        try:
            current_scroll = self.driver.execute_script("return document.documentElement.scrollTop || document.body.scrollTop")
            viewport_height = self.driver.execute_script("return window.innerHeight")
            element_rect = product.rect
            element_position = element_rect['y']
            
            if not (current_scroll <= element_position <= current_scroll + viewport_height):
                return None
                
            name = product.find_element(By.CLASS_NAME, "TicketItem_goodsName__Ju76j").text
            
            if name in self.processed_items:
                return None
                
            count += 1
            print(f"\n[{count}번째 전시회]")
            self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", product)
            time.sleep(0.5)
            
            exhibition_info = {
                "name": name,
                "details": {}
            }
            
            self._collect_detail_page_info(product, exhibition_info)
            
            self.processed_items.add(name)
            self.image_processor.combine_and_save_images(name)
            print(f"{name} 전시회 정보 수집 완료")
            return exhibition_info

        except Exception as e:
            print(f"항목 처리 중 오류: {str(e)}")
            return None

    def _collect_detail_page_info(self, product, exhibition_info):
        main_window = self.driver.current_window_handle
        product.click()
        time.sleep(1)
        
        windows = self.driver.window_handles
        for window in windows:
            if window != main_window:
                self.driver.switch_to.window(window)
                time.sleep(1)

                current_url = self.driver.current_url
                exhibition_info["detail_url"] = current_url
                
                try:
                    self._collect_basic_info(exhibition_info)
                    self._collect_detailed_info(exhibition_info, exhibition_info["name"])
                    self._collect_statistics(exhibition_info)
                    
                except Exception as detail_error:
                    print(f"상세 정보 수집 중 오류: {str(detail_error)}")
                    exhibition_info["details"]["상세정보"] = {}
                
                self.driver.close()
                self.driver.switch_to.window(main_window)

    def _collect_basic_info(self, exhibition_info):
        # 포스터 이미지 URL 추출
        poster_img = self.driver.find_element(By.CSS_SELECTOR, ".posterBoxImage")
        poster_url = poster_img.get_attribute('src')
        if poster_url and poster_url.startswith("//"):
            poster_url = "https:" + poster_url
        exhibition_info["poster_url"] = poster_url
        
        # 티켓캐스트 정보 수집
        try:
            ticket_cast = self.driver.find_element(By.CLASS_NAME, "prdCastNum").text
            exhibition_info["details"]["티켓캐스트"] = ticket_cast
        except:
            exhibition_info["details"]["티켓캐스트"] = "0"
        
        # 기본 정보 수집
        info_list = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "ul.info"))
        )
        info_items = info_list.find_elements(By.CSS_SELECTOR, "li.infoItem")
        
        for item in info_items:
            self._process_info_item(item, exhibition_info)

    def _process_info_item(self, item, exhibition_info):
        label = item.find_element(By.CSS_SELECTOR, ".infoLabel").text.strip()
        
        if label == "장소":
            place_detail = item.find_element(By.CSS_SELECTOR, ".infoDesc a").text.strip()
            exhibition_info["details"]["장소"] = place_detail
        
        elif label == "기간":
            period = item.find_element(By.CSS_SELECTOR, ".infoText").text.strip()
            exhibition_info["details"]["기간"] = period
        
        elif label == "관람연령":
            age = item.find_element(By.CSS_SELECTOR, ".infoText").text.strip()
            exhibition_info["details"]["관람연령"] = age
        
        elif label == "가격":
            self._process_price_info(item, exhibition_info)

    def _process_price_info(self, item, exhibition_info):
        try:
            prices = []
            price_detail = item.find_elements(By.CSS_SELECTOR, ".prdPriceDetail div")
            if price_detail:
                price_text = price_detail[0].text.strip()
                if price_text:
                    price_lines = price_text.split('\n')
                    for line in price_lines:
                        if '원' in line:
                            parts = line.strip().split('원')[0].split()
                            price_name = ' '.join(parts[:-1])
                            price_value = parts[-1].replace(',', '') + '원'
                            prices.append({
                                "name": price_name,
                                "price": price_value
                            })

            if not prices:
                price_items = item.find_elements(By.CSS_SELECTOR, ".infoPriceItem")
                for price_item in price_items[1:]:
                    try:
                        price_name = price_item.find_element(By.CSS_SELECTOR, ".name").text.strip()
                        price_value = price_item.find_element(By.CSS_SELECTOR, ".price").text.strip()
                        if price_name and price_value:
                            prices.append({
                                "name": price_name,
                                "price": price_value
                            })
                    except:
                        continue
            
            exhibition_info["details"]["가격"] = prices
            
        except Exception as price_error:
            print(f"가격 정보 파싱 중 오류: {str(price_error)}")
            exhibition_info["details"]["가격"] = []

    def _collect_detailed_info(self, exhibition_info, name):
        try:
            info_tab = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "a.navLink[data-target='INFO']"))
            )
            self.driver.execute_script("arguments[0].scrollIntoView(true);", info_tab)
            time.sleep(1)
            self.driver.execute_script("arguments[0].click();", info_tab)
            time.sleep(2)
            
            contents = self.driver.find_elements(By.CSS_SELECTOR, "div.prdContents.detail > div.content")
            content_info = {}
            
            for content in contents:
                self._process_content_section(content, content_info, name)
            
            exhibition_info["details"]["상세정보"] = content_info
            
        except Exception as tab_error:
            print(f"이용정보 탭 클릭 중 오류: {str(tab_error)}")

    def _process_content_section(self, content, content_info, name):
        try:
            title = content.find_element(By.CSS_SELECTOR, "h3.contentTitle").text.strip()
            
            if title == "관람시간 정보":
                text_parts = []
                detail = content.find_element(By.CSS_SELECTOR, "div.contentDetail")
                text = detail.find_element(By.CSS_SELECTOR, "p.contentDetailText").text.strip()
                text_parts.append(text)
                list_text = detail.find_element(By.CSS_SELECTOR, "ul.contentDetailList div").text.strip()
                text_parts.append(list_text)
                content_info[title] = "\n".join(text_parts)
            
            elif title == "공지사항":
                detail = content.find_element(By.CSS_SELECTOR, "div.contentDetail")
                content_info[title] = detail.text.strip()
            
            elif title == "할인정보":
                detail = content.find_element(By.CSS_SELECTOR, "div.contentDetail")
                discount_divs = detail.find_elements(By.CSS_SELECTOR, "div")
                content_info[title] = "\n".join([div.text.strip() for div in discount_divs if div.text.strip()])
            
            elif title == "상세정보":
                detail = content.find_element(By.CSS_SELECTOR, "div.contentDetail")
                images = []
                img_elements = detail.find_elements(By.TAG_NAME, "img")
                
                for img in img_elements:
                    img_url = img.get_attribute('src')
                    if img_url and img_url.startswith("//"):
                        img_url = "https:" + img_url
                    if img_url:
                        images.append(img_url)
                        self.image_processor.save_image(img_url, name, len(images))
                
                content_info["상세정보"] = {
                    "text": detail.text.strip(),
                    "images": images
                }
                
        except Exception as content_error:
            print(f"{title} 처리 중 오류: {str(content_error)}")

    def _collect_statistics(self, exhibition_info):
        try:
            stat_wrap = self.driver.find_element(By.CSS_SELECTOR, "div.statWrap")
            stats = {
                "성별": {},
                "연령": {}
            }
            
            gender_section = stat_wrap.find_element(By.CSS_SELECTOR, "div.statGender")
            gender_types = gender_section.find_elements(By.CSS_SELECTOR, "div.statGenderType")
            for gender in gender_types:
                gender_name = gender.find_element(By.CSS_SELECTOR, "div.statGenderName").text
                gender_value = gender.find_element(By.CSS_SELECTOR, "div.statGenderValue").text
                stats["성별"][gender_name] = gender_value
            
            age_section = stat_wrap.find_element(By.CSS_SELECTOR, "div.statAge")
            age_types = age_section.find_elements(By.CSS_SELECTOR, "div.statAgeType")
            for age in age_types:
                age_name = age.find_element(By.CSS_SELECTOR, "div.statAgeName").text
                age_percent = age.find_element(By.CSS_SELECTOR, "div.statAgePercent").text
                stats["연령"][age_name] = age_percent
            
            exhibition_info["details"]["예매자통계"] = stats
            
        except Exception as stat_error:
            print(f"예매자 통계 처리 중 오류: {str(stat_error)}")
            exhibition_info["details"]["예매자통계"] = "통계 정보 없음"

    def format_data(self):
        formatted_data = []
        for exhibition in self.exhibition_data:
            price_list = []
            if exhibition["details"].get("가격"):
                for price_item in exhibition["details"]["가격"]:
                    price_dict = {
                        "type": price_item["name"],
                        "price": int(''.join(filter(str.isdigit, price_item["price"])))
                    }
                    price_list.append(price_dict)

            formatted_exhibition = {
                "E_title": exhibition["name"],
                "E_context": exhibition["details"]["상세정보"].get("text", ""),
                "E_poster": exhibition.get("poster_url", ""),
                "E_price": price_list,
                "E_place": exhibition["details"].get("장소", "").replace("(자세히)", "").strip(),
                "E_date": exhibition["details"].get("기간", ""),
                "E_link": exhibition.get("detail_url", ""),
                "E_ticketcast": exhibition["details"].get("티켓캐스트", "0")
            }
            formatted_data.append(formatted_exhibition)
        return formatted_data

class OCRProcessor:
    def __init__(self):
        self.reader = easyocr.Reader(['en', 'ko'])
        self.results = {}

    def process_exhibition_images(self, image_processor):
        for name, segments in image_processor.processed_images.items():
            print(f"\n{name} OCR 처리 중...")
            
            try:
                # 바로 OCR 처리 수행
                results = self._process_image_group(segments)
                
                # 결과 저장 (메모리에만 저장)
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
                
                print(f"OCR 처리 완료: {name}")
                
            except Exception as e:
                print(f"OCR 처리 중 오류 발생: {str(e)}")
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
        load_dotenv()
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        if not self.openai_api_key:
            raise ValueError("OpenAI API 키가 설정되지 않았습니다.")
        openai.api_key = self.openai_api_key
        self.prompt_cache = {}

    @staticmethod
    def _sanitize_filename(filename):
        return sanitize_filename(filename)

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
            response = openai.chat.completions.create(
                model='gpt-4o-mini',
                messages=[
                    {"role": "user", "content": prompt + "\n" + "\n".join(ocr_texts)},
                ]
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"프롬프트 처리 중 오류 발생: {str(e)}")
            return None

class ExhibitionCrawler:
    def __init__(self):
        self.driver = DriverManager.create_driver()
        self.image_processor = ImageProcessor()
        self.data_collector = ExhibitionDataCollector(self.driver, self.image_processor)
        self.ocr_processor = OCRProcessor()
        self.prompt_processor = PromptProcessor()
        self.data_dir = os.path.join(os.getcwd(), "data")
        os.makedirs(self.data_dir, exist_ok=True)

    def start_crawling(self):
        try:
            print("크롤링을 시작합니다...")
            self.driver.maximize_window()
            self.driver.get("https://tickets.interpark.com/contents/genre/exhibition")
            
            # 페이지 로딩 대기 추가
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//button[contains(@class, 'genre-tab-item') and contains(@aria-label, '전시회')]"))
            ).click()
            
            # 페이지 안정화를 위한 대기
            time.sleep(3)
            
            # 전시회 정보 수집
            exhibition_data = self._get_exhibition_info()
            
            if not exhibition_data:
                print("수집된 전시회 정보가 없습니다.")
                return None
                
            # OCR 처리
            self.ocr_processor.process_exhibition_images(self.image_processor)
            
            # 데이터 포맷팅 및 저장
            formatted_data = self.format_and_save_data()
            return formatted_data
            
        except Exception as e:
            print(f"크롤링 중 오류 발생: {str(e)}")
            return None

    def _get_exhibition_info(self):
        scroll_step = 300
        count = 0
        # max_items = 5
        print("전시회 정보 수집을 시작합니다...")
        
        # while max_items > count:
        while True:
            try:
                products = self.driver.find_elements(By.CSS_SELECTOR, ".TicketItem_ticketItem__H51Vs")
                current_scroll = self.driver.execute_script("return document.documentElement.scrollTop || document.body.scrollTop")
                viewport_height = self.driver.execute_script("return window.innerHeight")
                found_new_items = False
                
                for product in products:
                    exhibition_info = self.data_collector.collect_exhibition_details(product, count)
                    if exhibition_info:
                        self.data_collector.exhibition_data.append(exhibition_info)
                        found_new_items = True
                        count += 1
                        # if count >= max_items:
                        #    break
                
                if not found_new_items:
                    if not self._scroll_page(current_scroll, scroll_step, viewport_height):
                        break
                        
            except Exception as e:
                print(f"오류 발생: {str(e)}")
                continue

        return self.data_collector.exhibition_data

    def _scroll_page(self, current_scroll, scroll_step, viewport_height):
        previous_scroll = current_scroll
        
        self.driver.execute_script("""
            window.scrollTo({
                top: arguments[0],
                behavior: 'smooth'
            });
        """, previous_scroll + scroll_step)
        
        time.sleep(1.5)
        
        new_scroll = self.driver.execute_script("return document.documentElement.scrollTop || document.body.scrollTop")
        page_height = self.driver.execute_script("return document.documentElement.scrollHeight")
        
        if new_scroll >= page_height - viewport_height or new_scroll == previous_scroll:
            print("\n페이지 끝에 도달했습니다.")
            return False
        return True

    def format_and_save_data(self):
        formatted_data = self.data_collector.format_data()
        
        for event in formatted_data:
            title = event["E_title"]
            
            # OCR 결과를 메모리에서 직접 가져옴
            if title in self.ocr_processor.results:
                ocr_texts = self.ocr_processor.results[title]['texts_only']['texts']
                prompt_result = self.prompt_processor.process_ocr_results(ocr_texts)
                if prompt_result:
                    event["E_context"] = prompt_result
                else:
                    print(f"프롬프트 처리 실패: {title}")
            else:
                print(f"OCR 결과를 찾을 수 없음: {title}")
        
        # 최종 결과만 저장
        output_path = os.path.join(self.data_dir, "exhibition_data.json")
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(formatted_data, f, ensure_ascii=False, indent=2)
        
        return formatted_data

    def _save_to_json(self, data, filename='exhibition_data.json'):
        file_path = os.path.join(self.data_dir, filename)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def close(self):
        self.driver.quit()

def main():
    crawler = ExhibitionCrawler()
    try:
        crawler.start_crawling()
    finally:
        crawler.close()

if __name__ == "__main__":
    main()
    