from exhibition_crawler.collectors.chrome_driver import DriverManager
from exhibition_crawler.collectors.exhibition_collector import ExhibitionDataCollector
from exhibition_crawler.processors.image_processor import ImageProcessor
from exhibition_crawler.processors.data_processor import OCRProcessor, PromptProcessor
from exhibition_crawler.processors.embedding import TextEmbedding
from exhibition_crawler.utils.mongoDB import MongoDBManager
import logging
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

logging.basicConfig(level=logging.INFO)

class ExhibitionCrawler:
    def __init__(self):
        self.driver = DriverManager.create_driver()
        self.image_processor = ImageProcessor()
        self.data_collector = ExhibitionDataCollector(self.driver, self.image_processor)
        self.ocr_processor = OCRProcessor()
        self.prompt_processor = PromptProcessor()
        self.text_embedder = TextEmbedding()
        self.mongodb_manager = MongoDBManager()

    def start_crawling(self):
        try:
            logging.info("크롤링을 시작합니다...")
            self.driver.maximize_window()
            self.driver.get("https://tickets.interpark.com/contents/genre/exhibition")
            
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//button[contains(@class, 'genre-tab-item') and contains(@aria-label, '전시회')]"))
            ).click()
            
            time.sleep(3)
            
            self.mongodb_manager.clear_collections()
            
            exhibition_data = self._get_exhibition_info()
            
            if not exhibition_data:
                logging.warning("수집된 전시회 정보가 없습니다.")
                return None
                
            self.ocr_processor.process_exhibition_images(self.image_processor)
            
            self.process_and_save_to_mongodb()
            return True
            
        except Exception as e:
            logging.error(f"크롤링 중 오류 발생: {str(e)}")
            return None

    def _get_exhibition_info(self):
        scroll_step = 300
        count = 0
        # max_items = 3
        
        logging.info("전시회 정보 수집을 시작합니다...")
        
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
                        # return self.data_collector.exhibition_data
                
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
            logging.info("\n페이지 끝에 도달했습니다.")
            return False
        return True

    def process_and_save_to_mongodb(self):
        formatted_data = self.data_collector.format_data()
        processed_data = []

        for event in formatted_data:
            title = event["E_title"]
            if title in self.ocr_processor.results:
                ocr_texts = self.ocr_processor.results[title]['texts_only']['texts']
                context = self.prompt_processor.process_ocr_results(ocr_texts)
                # context가 유효한 경우에만 데이터 추가
                if context and context.strip():
                    event["E_context"] = context
                    processed_data.append(event)
            else:
                logging.warning(f"'{title}' OCR 결과를 찾을 수 없습니다.")

        if not processed_data:
            logging.warning("저장할 유효한 데이터가 없습니다.")
            return

        inserted_ids = self.mongodb_manager.insert_exhibition_data(processed_data)
        if not inserted_ids:
            return

        # 임베딩 처리
        for event, original_id in zip(processed_data, inserted_ids):
            context = event.get("E_context", "")
            # context 재확인
            if context and context.strip():
                try:
                    embedding = self.text_embedder.get_embedding(context)
                    vector_data = {
                        "text": context,
                        "embedding": embedding
                    }
                    self.mongodb_manager.insert_vector_data(vector_data, original_id)
                except Exception as e:
                    logging.error(f"임베딩 처리 중 오류 발생: {str(e)}")
                    continue

        logging.info(f"유효한 context를 가진 데이터 {len(processed_data)}개가 MongoDB에 저장되었습니다.")
        logging.info(f"임베딩이 완료된 데이터 {len(inserted_ids)}개가 MongoDB에 저장되었습니다.")

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