from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
import time
import datetime
import csv
from flask import Flask, render_template, request, send_file
import os
from selenium.webdriver.firefox.options import Options

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        from_date = request.form['from_date']
        county = request.form['county']
        # working county url_ids: MiddlesexNorth, MiddlesexSouth, BerkSouth, BerkNorth, BerkMiddle, Hampshire, Franklin, Dukes, Suffolk, Worcester, Nantucket
        url = "https://www.masslandrecords.com/" + county + "/"
        data = [["Doc. #", "Rec Date", "Rec Time", "Type Desc.", "# of Pgs.", "Book/Page", "Consideration", "Doc. Status", "Price", "Town", "Street #", "Street Name", "Description", "Grantor/Grantee"]]
        #from_date = "10/01/2023"
        num_records_per_page = 3 #out of 100

        options = Options()
        options.add_argument("--headless") #comment out this line if you want firefox window
        driver = webdriver.Firefox(options=options)
        driver.get(url)

        time.sleep(2)

        #Search sequence
        driver.find_element(By.ID,"Navigator1_SearchCriteria1_menuLabel").click()
        WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.ID, "Navigator1_SearchCriteria1_LinkButton04"))).click()
        time.sleep(1)
        from_element = driver.find_element(By.ID,"SearchFormEx1_ACSTextBox_DateFrom")
        from_element.clear()
        from_element.send_keys(from_date)
        to_element = driver.find_element(By.ID,"SearchFormEx1_ACSTextBox_DateTo")
        to_element.clear()
        to_element.send_keys(datetime.date.today().strftime("%m/%d/%Y"))
        select = Select(driver.find_element(By.ID, 'SearchFormEx1_ACSDropDownList_DocumentType'))
        select.select_by_visible_text('DEED')
        #select.select_by_value("197")
        time.sleep(1)
        driver.find_element(By.NAME,"SearchFormEx1$btnSearch").click()

        #click 100 records per page
        time.sleep(2)
        WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.ID, "DocList1_PageView5Btn"))).click()
        time.sleep(1)

        #get data from individual records and store in array
        def getInfo(town):
            town = driver.find_element(By.ID, 'DocList1_GridView_Document_ctl0' + str(town+1) + '_ButtonRow_Town_' + str(town-1))

            table_id = driver.find_element(By.ID, 'DocDetails1_Table_Details')
            row = table_id.find_element(By.TAG_NAME, "tr")
            col = row.find_elements(By.TAG_NAME, "td")[0].text
            arr1 = col.split("\n")[1].split(" ", 7)

            table_id = driver.find_element(By.ID, 'DocDetails1_Table_Properties')
            row = table_id.find_element(By.TAG_NAME, "tr")
            col = row.find_elements(By.TAG_NAME, "td")[0].text
            arr2 = col.split("\n")[1].split(" ", 2)

            table_id = driver.find_element(By.ID, 'DocDetails1_GridView_GrantorGrantee')
            rows = table_id.find_elements(By.TAG_NAME, "tr")
            arr3 = []

            for row in rows:
                try:
                    col1 = row.find_elements(By.TAG_NAME, "td")[0].text
                    col2 = row.find_elements(By.TAG_NAME, "td")[1].text
                    arr3.append(col1+ " " +col2)
                except:
                    pass
            data.append(arr1+["Price not avaliable",town.text]+arr2+arr3)

        #loop through pages and records
        for j in range(2, 21, 2):
            try:
                for i in range(1, num_records_per_page+1):
                    if i < 9:
                        WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.ID, "DocList1_GridView_Document_ctl0"+str(i+1)+"_ButtonRow_Rec. Date_"+str(i-1)))).click()
                    else:
                        WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.ID, "DocList1_GridView_Document_ctl"+str(i+1)+"_ButtonRow_Rec. Date_"+str(i-1)))).click()
                    time.sleep(1)
                    try:
                        getInfo(i)
                    except:
                        pass
                    time.sleep(1)
                WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.ID, "DocList1_ctl02_ctl0"+str(j)+"_LinkButtonNumber"))).click()
            except:
                break

        csv_path = os.path.join('clean_data.csv')
        
        for i in range(0, len(data)):
            try:
                url = "https://www.homes.com/" #addresses[i]
                driver.get(url)
                time.sleep(1)
                from_element = driver.find_element("xpath", "//input[@aria-label='Place, Neighborhood, School or Agent']")
                from_element.clear()
                from_element.send_keys(data[i][10] + " " + data[i][11] + " " + data[i][12][:3] + "," + data[i][9] + ", MA")
                time.sleep(1)
                driver.find_element(By.ID, 'propertySearchBtn').click()
                time.sleep(1)
                price = driver.find_element(By.ID, 'price')
                data[i][8] = price.text
            except:
                data[i][8] = "Price not avaliable"
                pass

        driver.quit()

        with open(csv_path, 'w', newline='') as csvfile:   
            csvwriter = csv.writer(csvfile)
            csvwriter.writerows(data)

        return send_file(csv_path, as_attachment=True, download_name='clean_data.csv')
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)