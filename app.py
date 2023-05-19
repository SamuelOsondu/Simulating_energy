import simpy
from flask import render_template, Flask, request

app = Flask(__name__)


class HybridEnergySystem(object):
    def __init__(self, env, solar_area, battery_capacity, biomass_capacity, solar_cost, battery_cost, biomass_cost):
        self.env = env
        self.solar_area = solar_area
        self.battery_capacity = battery_capacity
        self.biomass_capacity = biomass_capacity
        self.battery_soc = 0.20  # Initial battery state of charge
        self.battery_energy = self.battery_soc * battery_capacity
        self.total_cost = 0
        self.solar_cost = solar_cost
        self.battery_cost = battery_cost
        self.biomass_cost = biomass_cost

    def solar(self):
        loads = [
            1.4, 1.4, 1.4, 1.4, 2.4, 2.6, 3.2, 9.975, 7.775, 7.075, 6.375,
            6.375, 8.075, 5.075, 8.075, 9.575, 9.575, 8.9, 10.4, 10.8, 10.8,
            5.8, 2.4, 1.4
        ]
        solar_insolation = 3.91
        efficiency = 0.95

        table = []  # Empty list to store simulation results

        for hour in range(24):
            load = loads[hour]
            epvg = self.solar_area * 0.15 * solar_insolation
            epvg_inv = epvg * efficiency
            enet = 0
            bmg_status = 'OFF'
            eunmet = 0
            ebattery = 0
            e_surplus = 0
            sink = 0
            if epvg_inv >= load >= 0:
                e_surplus = epvg_inv - load
                cost = self.solar_cost * epvg_inv
                self.total_cost += cost
                # Shouldn't it be the used epv itself?
                if self.battery_soc != 1:
                    ebattery = 0.99 * e_surplus
                    self.battery_energy = ebattery + self.battery_energy
                    self.battery_soc = self.battery_energy / self.battery_capacity
                else:
                    sink = e_surplus

            else:
                enet = load - epvg_inv
                cost = self.solar_cost * epvg_inv
                self.total_cost += cost

                ebattery = 1.00 * self.battery_energy
                if self.battery_soc >= 0.2 and ebattery >= enet:
                    cost = self.battery_cost * enet
                    self.total_cost += cost
                    self.battery_energy = ebattery - enet
                    self.battery_soc = self.battery_energy / self.battery_capacity
                else:
                    bmg_status = "ON"
                    cost = self.biomass_cost * enet
                    self.total_cost += cost
                    if self.biomass_capacity < enet:
                        eunmet = enet - self.biomass_capacity

                    else:
                        enet = self.biomass_capacity - enet
            table.append([
                hour, load, epvg, epvg_inv, enet, e_surplus, ebattery, self.battery_energy, self.battery_soc,
                self.biomass_capacity, bmg_status,
                eunmet, sink, cost
            ])

        return table


@app.route('/', methods=['GET', 'POST'])
def simulator():
    env = simpy.Environment()

    if request.method == 'POST':
        solar_area = float(request.form['solar_area'])
        battery_capacity = float(request.form['battery_capacity'])
        biomass_capacity = float(request.form['biomass_capacity'])
        solar_cost = float(request.form['solar_cost'])
        battery_cost = float(request.form['battery_cost'])
        biomass_cost = float(request.form['biomass_cost'])
        energy_system = HybridEnergySystem(env, solar_area, battery_capacity, biomass_capacity, solar_cost,
                                           battery_cost, biomass_cost)
        result_table = energy_system.solar()
        #
        # for row in result_table:
        #     formatted_row = []
        #     for value in row:
        #         if isinstance(value, str):
        #             formatted_row.append(value)
        #         else:
        #             formatted_row.append(f"{value:.4f}")
        #     print("\t".join(formatted_row))
        #
        #     if row[0] == 23:
        #         break  # Stop the simulation after hour 23
        #     #
        #
        # headers = ["Time", "Eload", "Epvg", "EpvgI", "Enet", "Esur", "BAT-I", "BA-L", "BA_SOC", "Ebmg", "BMGS", "Eunm",
        #            "Esi",
        #            "Cost"]

        return render_template('output.html', results=result_table)
    return render_template('input.html')


if __name__ == '__main__':
    app.run(debug=True)

