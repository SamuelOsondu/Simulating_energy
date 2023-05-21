from flask import render_template, Flask, request

app = Flask(__name__)


class HybridEnergySystem(object):
    def __init__(self, solar_area, battery_capacity, biomass_capacity, solar_cost, battery_cost, biomass_cost, initial_batterysoc):
        self.solar_area = solar_area
        self.battery_capacity = battery_capacity
        self.biomass_capacity = biomass_capacity
        self.battery_soc = initial_batterysoc
        self.battery_energy = self.battery_soc * self.battery_capacity
        self.solar_cost = solar_cost
        self.battery_cost = battery_cost
        self.biomass_cost = biomass_cost

    def solar(self):
        loads = [
            3.4, 3.4, 3.4, 3.4, 4.4, 4.6, 5.2, 11.975, 9.775, 9.075, 8.375,
            8.375, 10.075, 7.075, 10.075, 11.575, 11.575, 10.9, 12.4, 12.8, 12.8,
            7.8, 4.4, 3.4
        ]

        solar_insolation = [
            0, 0, 0, 0, 0, 0, 0, 0, 0.15, 0.5, 1.0, 2.346, 3.91, 3.91,
            3.91, 3.91, 0.5, 0.10, 0, 0, 0, 0, 0, 0
        ]
        time_range = [
            "0:00-1:00", "1:00-2:00", "2:00-3:00", "3:00-4:00", "4:00-5:00", "5:00-6:00",
            "6:00-7:00", "7:00-8:00", "8:00-9:00", "9:00-10:00", "10:00-11:00", "11:00-12:00",
            "12:00-13:00", "13:00-14:00", "14:00-15:00", "15:00-16:00", "16:00-17:00", "17:00-18:00",
            "18:00-19:00", "19:00-20:00", "20:00-21:00", "21:00", "22:00-23:00", "23:00-24:00"
        ]

        table = []  # Empty list to store simulation results

        for hour in range(24):
            load = loads[hour]
            epvg = self.solar_area * 0.15 * solar_insolation[hour]
            epvg_inv = epvg * 0.95
            bmg_status = 'OFF'
            solar_surplus = 0
            batt_inv = 0
            eunmet = 0
            sink = 0
            enet = 0
            cost = 0

            # Drawing from the solar energy if sufficient and discharging the solar
            if epvg_inv >= load > 0:
                solar_surplus = epvg_inv - load
                cost = self.solar_cost * epvg
                # Charging the battery
                if solar_surplus > 0:
                    batterycharge_left = self.battery_capacity - self.battery_energy
                    if batterycharge_left > 0:
                        if solar_surplus >= batterycharge_left:
                            solar_surplus -= batterycharge_left
                            self.battery_energy += (batterycharge_left * 0.99)
                            self.battery_soc = self.battery_energy / self.battery_capacity
                            sink = solar_surplus
                        else:
                            batterycharge_left -= solar_surplus
                            self.battery_energy += (solar_surplus * 0.99)
                            self.battery_soc = self.battery_energy / self.battery_capacity
                    else:
                        # Powering the sink cause of surplus solar after charging the battery
                        sink = solar_surplus

            else:
                # Drawing the max available solar energy
                cost = self.solar_cost * epvg
                enet = load - epvg_inv
                # epvg_inv = 0

                # Discharging from battery
                if self.battery_soc >= 0.2 and self.battery_energy >= enet:
                    self.battery_energy -= enet
                    cost = self.battery_cost * enet
                     
                    self.battery_soc = self.battery_energy / self.battery_capacity
                    batt_inv += enet
                else:
                    bmg_status = "ON"
                    cost = self.biomass_cost * self.biomass_capacity
                     
                    # Discharging the enet with the availaible biomass and adding the unmet
                    if self.biomass_capacity < enet:
                        # enet -= self.biomass_capacity
                        eunmet = enet - self.biomass_capacity

                    else:
                        bmg_left = self.biomass_capacity - enet
                        # enet = 0
                        if bmg_left > 0:
                            batterycharge_left = self.battery_capacity - self.battery_energy
                            if batterycharge_left > 0:
                                if bmg_left >= batterycharge_left:
                                    bmg_left -= batterycharge_left
                                    self.battery_energy += batterycharge_left
                                    self.battery_soc = self.battery_energy / self.battery_capacity
                                    sink = bmg_left
                                else:
                                    batterycharge_left -= bmg_left

            def convert_to_decimal_places(input_list):
                converted_list = []
                for num in input_list:
                    converted_num = "{:.2f}".format(num)
                    converted_list.append(converted_num)
                return converted_list

            formatted_list = convert_to_decimal_places([
                epvg, epvg_inv, enet, solar_surplus, batt_inv, self.battery_energy, self.battery_soc,
                self.biomass_capacity, eunmet, sink, cost, load
            ])

            table.append([
                time_range[hour], formatted_list[11], formatted_list[0], formatted_list[1], formatted_list[2], formatted_list[3],
                formatted_list[4], formatted_list[5], formatted_list[6], formatted_list[7], bmg_status,
                formatted_list[8], formatted_list[9], formatted_list[10],
            ])

        return table


@app.route('/', methods=['GET', 'POST'])
def simulator():

    if request.method == 'POST':
        solar_area = float(request.form['solar_area'])
        battery_capacity = float(request.form['battery_capacity'])
        biomass_capacity = float(request.form['biomass_capacity'])
        solar_cost = float(request.form['solar_cost'])
        battery_cost = float(request.form['battery_cost'])
        biomass_cost = float(request.form['biomass_cost'])
        initial_batterysoc = float(request.form['initial_batterysoc'])
        energy_system = HybridEnergySystem(solar_area, battery_capacity, biomass_capacity, solar_cost,
                                           battery_cost, biomass_cost, initial_batterysoc)
        result_table = energy_system.solar()

        return render_template('output.html', results=result_table)
    return render_template('input.html')


if __name__ == '__main__':
    app.run(debug=True)

