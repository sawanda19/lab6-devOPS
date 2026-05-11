# Модель: Автоматизоване складання розкладу занять — Генетичний алгоритм (5 семестр)
# Автор: Акімов Андрій, група АІ-231

from flask import Flask, request, jsonify
import random
import copy
from typing import List, Dict, Tuple

app = Flask(__name__)


class ScheduleData:
    def __init__(self, num_lecturers=15, num_subjects=30,
                 num_rooms=12, num_groups=10):
        self.num_lecturers  = num_lecturers
        self.num_subjects   = num_subjects
        self.num_rooms      = num_rooms
        self.num_groups     = num_groups
        self.days           = 5
        self.slots_per_day  = 6
        self.total_slots    = self.days * self.slots_per_day
        self.lecturers = self._generate_lecturers()
        self.subjects  = self._generate_subjects()
        self.rooms     = self._generate_rooms()
        self.groups    = self._generate_groups()

    def _generate_lecturers(self):
        return [{'id': i, 'name': f'Викладач_{i+1}',
                 'preferred_slots': random.sample(range(self.total_slots), random.randint(5, 15))}
                for i in range(self.num_lecturers)]

    def _generate_subjects(self):
        types = ['Лекція', 'Практика', 'Лабораторна']
        return [{'id': i, 'name': f'Дисципліна_{i+1}',
                 'type': random.choice(types),
                 'lecturer_id': random.randint(0, self.num_lecturers - 1),
                 'group_id':    random.randint(0, self.num_groups - 1),
                 'hours':       random.choice([2, 4])}
                for i in range(self.num_subjects)]

    def _generate_rooms(self):
        types = ["Лекційна", "Комп'ютерна", 'Лабораторія']
        return [{'id': i, 'name': f'Ауд_{100+i}',
                 'capacity': random.randint(20, 50),
                 'type': random.choice(types)}
                for i in range(self.num_rooms)]

    def _generate_groups(self):
        return [{'id': i, 'name': f'Група_{i+1}',
                 'size': random.randint(15, 30)}
                for i in range(self.num_groups)]


class ScheduleOptimizer:
    def __init__(self, data: ScheduleData, population_size=50,
                 max_iterations=200, mutation_rate=0.1):
        self.data            = data
        self.lambda1         = 1000
        self.lambda2         = 10
        self.lambda3         = 1
        self.population_size = population_size
        self.max_iterations  = max_iterations
        self.mutation_rate   = mutation_rate
        self.tournament_size = 3
        self.history: List[Dict] = []

    def create_random_schedule(self):
        return [{'subject_id':    s['id'],
                 'subject_name':  s['name'],
                 'lecturer_id':   s['lecturer_id'],
                 'lecturer_name': self.data.lecturers[s['lecturer_id']]['name'],
                 'group_id':      s['group_id'],
                 'group_name':    self.data.groups[s['group_id']]['name'],
                 'room_id':       random.randint(0, self.data.num_rooms - 1),
                 'time_slot':     random.randint(0, self.data.total_slots - 1),
                 'type':          s['type']}
                for s in self.data.subjects]

    def check_conflicts(self, schedule):
        conflicts = 0
        for slot in range(self.data.total_slots):
            for key in ('lecturer_id', 'room_id', 'group_id'):
                vals = [s[key] for s in schedule if s['time_slot'] == slot]
                conflicts += len(vals) - len(set(vals))
        for lid in range(self.data.num_lecturers):
            for day in range(self.data.days):
                ds, de = day * self.data.slots_per_day, (day+1) * self.data.slots_per_day
                c = [s for s in schedule if s['lecturer_id'] == lid and ds <= s['time_slot'] < de]
                if len(c) > 4:
                    conflicts += len(c) - 4
        return conflicts

    def calculate_gaps(self, schedule):
        gaps = 0
        for lid in range(self.data.num_lecturers):
            for day in range(self.data.days):
                ds, de = day * self.data.slots_per_day, (day+1) * self.data.slots_per_day
                slots = sorted([s['time_slot'] for s in schedule
                                if s['lecturer_id'] == lid and ds <= s['time_slot'] < de])
                for i in range(len(slots) - 1):
                    gaps += max(0, slots[i+1] - slots[i] - 1)
        return gaps

    def calculate_preferences(self, schedule):
        return sum(min(abs(a['time_slot'] - p)
                       for p in self.data.lecturers[a['lecturer_id']]['preferred_slots'])
                   for a in schedule
                   if a['time_slot'] not in self.data.lecturers[a['lecturer_id']]['preferred_slots'])

    def objective_function(self, schedule):
        return (self.lambda1 * self.check_conflicts(schedule) +
                self.lambda2 * self.calculate_gaps(schedule) +
                self.lambda3 * self.calculate_preferences(schedule))

    def optimize(self):
        population = [self.create_random_schedule() for _ in range(self.population_size)]
        best = min(population, key=self.objective_function)
        best_score = self.objective_function(best)

        for gen in range(self.max_iterations):
            scores   = [self.objective_function(s) for s in population]
            selected = []
            for _ in range(len(population) // 2):
                t = random.sample(list(zip(population, scores)), self.tournament_size)
                selected.append(copy.deepcopy(min(t, key=lambda x: x[1])[0]))

            new_pop = []
            for i in range(0, len(selected) - 1, 2):
                pt = random.randint(1, len(selected[i]) - 1)
                c1 = selected[i][:pt] + selected[i+1][pt:]
                c2 = selected[i+1][:pt] + selected[i][pt:]
                for c in (c1, c2):
                    if random.random() < self.mutation_rate:
                        a, b = random.sample(range(len(c)), 2)
                        c[a]['time_slot'], c[b]['time_slot'] = c[b]['time_slot'], c[a]['time_slot']
                new_pop.extend([c1, c2])

            population = sorted(new_pop + selected, key=self.objective_function)[:self.population_size]
            cur_score  = self.objective_function(population[0])
            if cur_score < best_score:
                best_score = cur_score
                best = copy.deepcopy(population[0])

            self.history.append({'generation': gen, 'best_score': best_score,
                                  'conflicts': self.check_conflicts(best)})
        return best


@app.route('/calculate', methods=['POST'])
def calculate():
    body = request.get_json(silent=True) or {}

    def bounded(v, d, lo, hi):
        try: return max(lo, min(hi, int(v)))
        except: return d

    def boundedf(v, d, lo, hi):
        try: return max(lo, min(hi, float(v)))
        except: return d

    num_lecturers   = bounded(body.get('num_lecturers'),   15,  2,  50)
    num_subjects    = bounded(body.get('num_subjects'),    30,  2, 100)
    num_rooms       = bounded(body.get('num_rooms'),       12,  2,  40)
    num_groups      = bounded(body.get('num_groups'),      10,  2,  30)
    population_size = bounded(body.get('population_size'), 50, 10, 500)
    max_iterations  = bounded(body.get('max_iterations'), 200,  1, 2000)
    mutation_rate   = boundedf(body.get('mutation_rate'), 0.1, 0.0, 1.0)

    data      = ScheduleData(num_lecturers, num_subjects, num_rooms, num_groups)
    optimizer = ScheduleOptimizer(data, population_size, max_iterations, mutation_rate)
    schedule  = optimizer.optimize()

    conflicts = optimizer.check_conflicts(schedule)
    gaps      = optimizer.calculate_gaps(schedule)
    prefs     = optimizer.calculate_preferences(schedule)
    score     = optimizer.objective_function(schedule)

    day_names = ['Понеділок', 'Вівторок', 'Середа', 'Четвер', "П'ятниця"]
    preview = []
    for item in schedule[:5]:
        room = data.rooms[item['room_id']]
        preview.append({
            'subject':  item['subject_name'],
            'type':     item['type'],
            'lecturer': item['lecturer_name'],
            'group':    item['group_name'],
            'room':     room['name'],
            'day':      day_names[item['time_slot'] // data.slots_per_day],
            'pair':     item['time_slot'] % data.slots_per_day + 1
        })

    return jsonify({
        "status": "success",
        "input": {
            "num_lecturers": num_lecturers, "num_subjects": num_subjects,
            "num_rooms": num_rooms, "num_groups": num_groups,
            "population_size": population_size, "max_iterations": max_iterations,
            "mutation_rate": mutation_rate
        },
        "result": {
            "conflicts": conflicts, "gaps": gaps,
            "preference_deviation": prefs, "final_score": round(score, 2),
            "iterations_done": len(optimizer.history),
            "schedule_size": len(schedule),
            "schedule_preview": preview
        }
    })


@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok", "model": "Genetic Algorithm Schedule Optimizer"})


if __name__ == '__main__':
    print("=" * 50)
    print(" Сервер запущено!")
    print(" POST http://127.0.0.1:5000/calculate")
    print(" GET  http://127.0.0.1:5000/health")
    print("=" * 50)
    app.run(host='0.0.0.0', port=5000, debug=True)
