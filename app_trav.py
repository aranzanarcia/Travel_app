import tkinter as tk
from tkinter import messagebox
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import requests
import re
import math
from PIL import Image, ImageTk
from io import BytesIO
from openai import OpenAI

# Define city_names, price_avg, and food_entry globally
city_names = []
price_avg = []
food_entry = None
city_selection_window = None

def chat_gpt_bot(place, month, food_t):
    client = OpenAI(api_key="your key here")
    completition = client.chat.completions.create(model="gpt-3.5-turbo", messages=[
        {"role": "system", "content": "Act as a travel agent"},
        {"role": "user", "content": f"Explain what the weather is gonna be like in {place} for the month {month} in a concise way, recommend what items to pack in the suitcase according to the place and month and give some recommendations of things to do. Also recommend 3 restaurants suited for {food_t} type of food.Put it in 4 lists called WEATHER, ITEMS TO BRING, ACTIVITIES AND RESTAURANTS, the weather list should be short and the activities list should have at least 4 acitivities and one of them should be something interesting and unusual"}
    ])
    return completition

def scrape_trip_com(month):
    url = f"https://www.trip.com/flights/explore?dcity=sto&ddate=2024-{month}-01,2024-{month}-30&flighttype=rt&class=y&quantity=1&searchboxarg=t&sort=price"
    options = webdriver.ChromeOptions()
    options.add_argument("--enable-javascript")
    driver = webdriver.Chrome(options)
    driver.maximize_window()
    driver.get(url)
    
    WebDriverWait(driver, 3)
    
    button = WebDriverWait(driver, 4).until(
        EC.element_to_be_clickable((By.XPATH, '//span[@class="f-14 f-bold title"][text()="Nonstop"]')))
    button.click()
    WebDriverWait(driver, 4)

    top_list_wrapper = driver.find_element("css selector", ".top-list-wrapper")
    driver.execute_script("arguments[0].scrollBy(0, 500);", top_list_wrapper)

    soup = BeautifulSoup(driver.page_source, "lxml")

    info_elements = driver.find_elements("css selector", ".top-list-flight__info")

    for info in info_elements:
        city_element = info.find_element("css selector", "span.top-list-flight__infoCity")
        city_name = city_element.text
        city_names.append(city_name)

        price_elements = info.find_elements("css selector", "span.price")
        if len(price_elements) == 1:
            price_1_text = price_elements[0].text
            price_avg.append(float(re.sub(r'[^\d.]', '', price_1_text)))
        elif len(price_elements) == 2:
            price_1_text = price_elements[0].text
            price_2_text = price_elements[1].text
            price_avg.append(math.ceil((float(re.sub(r'[^\d.]', '', price_1_text)) + float(re.sub(r'[^\d.]', '', price_2_text))) / 2))

    month_te = "September" if month == "09" else "October" if month == "10" else "November" if month == "11" else "December" if month =="12" else "January" if month == "01" else "February" if month == "02" else "March" if month == "03" else "April" if month == "04" else "May" if month == "05" else "June" if month == "06" else "July" if month == "07" else "August"
    driver.close()    
    return month_te

def get_food_preference(city, month_te):
    city_capitalized = city.capitalize()
    if city_capitalized in city_names:
        global food_entry  # Declare food_entry as global
        # Prompt user for food preference
        food_preference_window = tk.Toplevel()
        food_preference_window.title("Food Preference")

        food_label = tk.Label(food_preference_window, text="What type of food do you like?")
        food_label.grid(row=0, column=0, padx=10, pady=10)

        food_entry = tk.Entry(food_preference_window)
        food_entry.grid(row=0, column=1, padx=10, pady=10)

        confirm_food_button = tk.Button(food_preference_window, text="Confirm", command=lambda: on_food_confirm(city_capitalized, month_te))
        confirm_food_button.grid(row=1, column=0, columnspan=2, padx=10, pady=10)

        # Function to handle food preference confirmation
        def on_food_confirm(city, month_te):
            scrape_gimages(month_te, city)
            global food_entry  # Update to global scope
            food_preference = food_entry.get()  # Retrieve food preference
            food_preference_window.destroy()
            # Call chat_gpt_bot function with city, month, and food preference
            chat_response = chat_gpt_bot(city, month_te, food_preference)
            messagebox.showinfo("Recommendations", chat_response.choices[0].message.content)
            # Scrape images
            #scrape_gimages(month_te, city)
    else:
        messagebox.showerror("Error", "Invalid choice. Please select from the provided options.")

def on_accept(entry_month, accept_button):
    month = entry_month.get()
    month_te = scrape_trip_com(month)

    # Get travel options and display in messagebox
    message = f"\nThese are some of the best direct travel options departing from Stockholm in {month_te}:\n"
    message += "Note: *Prices do not disclose the real price of a ticket nor they include extra charges from airlines.*\n\n"
    for place, price in zip(city_names, price_avg):
        message += f"{place} - Average price: {price} US$ for {month_te}.\n"
    
    # Display travel options in messagebox
    messagebox.showinfo("Travel Options", message)

    # Prompt user to select a city
    global city_selection_window
    city_selection_window = tk.Toplevel()
    city_selection_window.title("City Selection")

    city_label = tk.Label(city_selection_window, text="Which city would you want to explore:")
    city_label.grid(row=0, column=0, padx=10, pady=10)

    city_entry = tk.Entry(city_selection_window)
    city_entry.grid(row=0, column=1, padx=10, pady=10)

    confirm_button = tk.Button(city_selection_window, text="Confirm", command=lambda: get_food_preference(city_entry.get(), month_te))
    confirm_button.grid(row=1, column=0, columnspan=2, padx=10, pady=10)

# Scrape and display images
def scrape_gimages(month_te, user_cho):
    url_1 = f"https://yandex.com/images/search?text={user_cho}%20place%20in%20{month_te}"
    driver = webdriver.Chrome()
    driver.maximize_window()
    driver.get(url_1)

    # Wait for the button to be clickable
    agree_button_selector = ".gdpr-popup-v3-button.gdpr-popup-v3-button_id_mandatory"
    agree_button = WebDriverWait(driver, 4).until(EC.element_to_be_clickable((By.CSS_SELECTOR, agree_button_selector)))

    # Click the agree button
    agree_button.click()
    images_selector = ".ContentImage-Image.ContentImage-Image_clickable"
    images = WebDriverWait(driver, 3).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, images_selector)))

    # Select the first image
    first_image = images[0]

    # Get the source URL of the first image
    image_url = first_image.get_attribute("src")

    # Retrieve the image content
    image_content = requests.get(image_url).content

    # Display the image using PIL
    image = Image.open(BytesIO(image_content))
    image = ImageTk.PhotoImage(image)

    # Display the image in a label widget
    image_label = tk.Label(city_selection_window, image=image)
    image_label.image = image
    image_label.grid(row=2, column=0, columnspan=2, padx=10, pady=10)

    driver.quit()

# Tkinter GUI
root = tk.Tk()
root.title("Travel Assistant")

label_month = tk.Label(root, text="Which month do you wanna travel in (01 - 12): ")
label_month.grid(row=0, column=0, padx=10, pady=10)

entry_month = tk.Entry(root)
entry_month.grid(row=0, column=1, padx=10, pady=10)

accept_button = tk.Button(root, text="Get options", command=lambda: on_accept(entry_month, accept_button))
accept_button.grid(row=1, column=0, columnspan=2, padx=10, pady=10, sticky="we")

root.mainloop()










