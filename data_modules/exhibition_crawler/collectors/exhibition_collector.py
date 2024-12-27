from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import logging

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
            logging.info(f"\n[{count}번째 전시회]")
            self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", product)
            time.sleep(0.5)
            
            exhibition_info = {
                "name": name,
                "details": {}
            }
            
            self._collect_detail_page_info(product, exhibition_info)
            
            self.processed_items.add(name)
            self.image_processor.combine_and_save_images(name)
            logging.info(f"{name} 전시회 정보 수집 완료")
            return exhibition_info

        except Exception as e:
            logging.error(f"항목 처리 중 오류: {str(e)}")
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
        poster_img = self.driver.find_element(By.CSS_SELECTOR, ".posterBoxImage")
        poster_url = poster_img.get_attribute('src')
        if poster_url and poster_url.startswith("//"):
            poster_url = "https:" + poster_url
        exhibition_info["poster_url"] = poster_url
        
        try:
            ticket_cast = self.driver.find_element(By.CLASS_NAME, "prdCastNum").text
            exhibition_info["details"]["티켓캐스트"] = ticket_cast
        except:
            exhibition_info["details"]["티켓캐스트"] = "0"
        
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
            price_dict = {}
            if exhibition["details"].get("가격"):
                for price_item in exhibition["details"]["가격"]:
                    price_value = int(''.join(filter(str.isdigit, price_item["price"])))
                    price_dict[price_item["name"]] = f"{price_value:,}원"

            formatted_exhibition = {
                "E_title": exhibition["name"],
                "E_context": exhibition["details"]["상세정보"].get("text", ""),
                "E_poster": exhibition.get("poster_url", ""),
                "E_price": price_dict,
                "E_place": exhibition["details"].get("장소", "").replace("(자세히)", "").strip(),
                "E_date": exhibition["details"].get("기간", ""),
                "E_link": exhibition.get("detail_url", ""),
                "E_ticketcast": exhibition["details"].get("티켓캐스트", "0")
            }
            formatted_data.append(formatted_exhibition)
        return formatted_data