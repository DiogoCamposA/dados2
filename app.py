from flask import Flask, render_template, request
import paho.mqtt.client as mqtt
import time
import datetime

app = Flask(__name__)

MQTT_BROKER_HOST = "broker.hivemq.com"
MQTT_BROKER_PORT = 1883
MQTT_TOPIC = "MQTTINCBTempUmidDiogo"

mqtt_values_monthly = {}
mqtt_values_daily = {}
mqtt_values_hourly = {}
mqtt_values = {}

def on_connect(client, userdata, flags, rc):
    print("Conectado ao servidor MQTT com código de resultado " + str(rc))
    client.subscribe(MQTT_TOPIC)

def on_message(client, userdata, msg):
    global mqtt_values_monthly, mqtt_values_daily, mqtt_values_hourly
    mqtt_data = msg.payload.decode()
    mqtt_data_1 = mqtt_data[13:-49]
    mqtt_data_2 = mqtt_data[34:-28]
    mqtt_data_3 = mqtt_data[59:-4]

    timestamp = int(time.time()) - 3 * 3600  # Calculate timestamp for 3 hours ago
    three_hours_ago = datetime.datetime.fromtimestamp(timestamp)
    month, day, hour = three_hours_ago.month, three_hours_ago.day, three_hours_ago.hour

    for metric, value in enumerate([mqtt_data_1, mqtt_data_2, mqtt_data_3], start=1):
        if month not in mqtt_values_monthly:
            mqtt_values_monthly[month] = {}
        if day not in mqtt_values_monthly[month]:
            mqtt_values_monthly[month][day] = {}
        if hour not in mqtt_values_monthly[month][day]:
            mqtt_values_monthly[month][day][hour] = {}
        if metric not in mqtt_values_monthly[month][day][hour]:
            mqtt_values_monthly[month][day][hour][metric] = []
        mqtt_values_monthly[month][day][hour][metric].append(float(value))

    for metric, value in enumerate([mqtt_data_1, mqtt_data_2, mqtt_data_3], start=1):
        if month not in mqtt_values:
            mqtt_values[month] = {}
        if day not in mqtt_values[month]:
            mqtt_values[month][day] = {}
        if metric not in mqtt_values[month][day]:
            mqtt_values[month][day][metric] = []
        mqtt_values[month][day][metric].append(float(value))

    for metric, value in enumerate([mqtt_data_1, mqtt_data_2, mqtt_data_3], start=1):
        if day not in mqtt_values_daily:
            mqtt_values_daily[day] = {}
        if hour not in mqtt_values_daily[day]:
            mqtt_values_daily[day][hour] = {}
        if metric not in mqtt_values_daily[day][hour]:
            mqtt_values_daily[day][hour][metric] = []
        mqtt_values_daily[day][hour][metric].append(float(value))

    for metric, value in enumerate([mqtt_data_1, mqtt_data_2, mqtt_data_3], start=1):
        if hour not in mqtt_values_hourly:
            mqtt_values_hourly[hour] = {}
        if metric not in mqtt_values_hourly[hour]:
            mqtt_values_hourly[hour][metric] = []
        mqtt_values_hourly[hour][metric].append(float(value))

    print(f"TEMPERATURA recebida e processada para o mês {month}, dia {day}, hora {hour}: {mqtt_data_1}")
    print(f"AR recebida e processada para o dia {day}, hora {hour}: {mqtt_data_2}")
    print(f"SOLO recebida e processada para a hora {hour}: {mqtt_data_3}")

# Configuração do cliente MQTT
mqtt_client = mqtt.Client()
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message
mqtt_client.connect(MQTT_BROKER_HOST, MQTT_BROKER_PORT, 60)

mqtt_client.loop_start()

def calcular_media(month, day, hour, metric):
    if (
        month in mqtt_values_monthly and
        day in mqtt_values_monthly[month] and
        hour in mqtt_values_monthly[month][day] and
        metric in mqtt_values_monthly[month][day][hour]
    ):
        values = mqtt_values_monthly[month][day][hour][metric]
        if values:
            return sum(values) / len(values)
    
    return 0.0

def calcular_media_dia(month, day, metric):
    global mqtt_values
    if (
        month in mqtt_values
        and day in mqtt_values[month]
        and metric in mqtt_values[month][day]
        and len(mqtt_values[month][day][metric]) > 0
    ):
        return sum(mqtt_values[month][day][metric]) / len(mqtt_values[month][day][metric])
    else:
        return 0.0 

def calcular_media_diaria(day, hour, metric):
    global mqtt_values_daily
    if (
        day in mqtt_values_daily
        and hour in mqtt_values_daily[day]
        and metric in mqtt_values_daily[day][hour]
        and len(mqtt_values_daily[day][hour][metric]) > 0
    ):
        return sum(mqtt_values_daily[day][hour][metric]) / len(mqtt_values_daily[day][hour][metric])
    else:
        return 0.0  

def calcular_media_hora(hour, metric):
    global mqtt_values_hourly
    if (
        hour in mqtt_values_hourly
        and metric in mqtt_values_hourly[hour]
        and len(mqtt_values_hourly[hour][metric]) > 0
    ):
        return sum(mqtt_values_hourly[hour][metric]) / len(mqtt_values_hourly[hour][metric])
    else:
        return 0.0  

@app.route("/")
def index():
    current_month = int(time.strftime("%m", time.localtime(time.time())))

    return render_template("index.html", current_month=current_month)

@app.route("/selecionar_dia")
def selecionar_dia():
    selected_month = int(request.args.get("month"))
    selected_day = int(request.args.get("day"))
    medias_por_hora = {}

    for hour in range(24):
        medias_por_hora[hour] = {
            "temp": calcular_media(selected_month, selected_day, hour, 1),
            "umid": calcular_media(selected_month, selected_day, hour, 2),
            "solo": calcular_media(selected_month, selected_day, hour, 3),
        }

    return render_template("selecionar_dia.html", selected_month=selected_month, selected_day=selected_day, medias_por_hora=medias_por_hora)

@app.route("/selecionar_mes", methods=["GET", "POST"])
def selecionar_mes():
    if request.method == "POST":
        selected_month = int(request.form["selected_month"])
        days_in_month = 31  

        medias_por_dia = {}

        for day in range(1, days_in_month + 1):
            medias_por_dia[day] = {
                "temp": calcular_media_dia(selected_month, day, 1),
                "umid": calcular_media_dia(selected_month, day, 2),
                "solo": calcular_media_dia(selected_month, day, 3),
            }

        return render_template("selecionar_mes.html", selected_month=selected_month, medias_por_dia=medias_por_dia)

    return render_template("selecionar_mes_input.html")

if __name__ == "__main__":
    app.run(debug=True)
