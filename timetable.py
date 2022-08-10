from ortools.sat.python import cp_model
#  Adapted from https://github.com/google/or-tools/blob/stable/examples/contrib/school_scheduling_sat.py


class SchoolSchedulingProblem(object):

    def __init__(self, subjects, teachers, curriculum, specialties, working_days,
                 periods, courses, teacher_work_hours):
        self.subjects = subjects
        self.teachers = teachers
        self.curriculum = curriculum
        self.specialties = specialties
        self.working_days = working_days
        self.periods = periods
        self.courses = courses
        self.teacher_work_hours = teacher_work_hours


class SchoolSchedulingSatSolver(object):

    def __init__(self, problem):

        self.problem = problem

        # Create a list of timeslots from days * periods
        self.timeslots = [
            '{0:10} {1:6}'.format(x, y)
            for x in problem.working_days
            for y in problem.periods
        ]

        # Variables for problem/constraints
        self.num_days = len(problem.working_days)
        self.num_periods = len(problem.periods)
        self.num_slots = len(self.timeslots)
        self.num_teachers = len(problem.teachers)
        self.num_subjects = len(problem.subjects)
        self.num_courses = len(problem.courses)

        all_courses = range(self.num_courses)
        all_teachers = range(self.num_teachers)
        all_slots = range(self.num_slots)
        all_subjects = range(self.num_subjects)

        self.model = cp_model.CpModel()

        #  Creates the main model variable and includes an
        #  indirect constraint of teacher can only tech their subject speciality
        self.assignment = {}
        for c in all_courses:
            for s in all_subjects:
                for t in all_teachers:
                    for slot in all_slots:
                        # If teacher is qualified to teach this subject, boolean variable (can be 0/false or 1/true)
                        if t in self.problem.specialties[s]:
                            name = 'C:{%i} S:{%i} T:{%i} Slot:{%i}' % (c, s, t, slot)
                            self.assignment[c, s, t, slot] = self.model.NewBoolVar(name)
                        # If teacher isn't qualified to teach this subject, can be a max of 0 (always 0/false)
                        else:
                            name = 'NO DISP C:{%i} S:{%i} T:{%i} Slot:{%i}' % (c, s, t, slot)
                            self.assignment[c, s, t, slot] = self.model.NewIntVar(0, 0, name)

        # Constraints

        # Each course must have the quantity of classes specified in the curriculum
        for course in all_courses:
            for subject in all_subjects:
                required_slots = self.problem.curriculum[self.problem.subjects[subject]]
                self.model.Add(
                    sum(self.assignment[course, subject, teacher, slot]
                        for slot in all_slots
                        for teacher in all_teachers) == required_slots)

        # Teacher can do at most one class at a time
        for teacher in all_teachers:
            for slot in all_slots:
                self.model.Add(
                    sum([
                        self.assignment[c, s, teacher, slot]
                        for c in all_courses
                        for s in all_subjects
                    ]) <= 1)

        # Each slot in each course can only have one class at a time
        for courses in all_courses:
            for slot in all_slots:
                self.model.Add(
                    sum([
                        self.assignment[courses, s, teacher, slot]
                        for s in all_subjects
                        for teacher in all_teachers
                    ]) <= 1)

        # Maximum work hours for each teacher
        for teacher in all_teachers:
            self.model.Add(
                sum([
                    self.assignment[c, s, teacher, slot] for c in all_courses
                    for s in all_subjects for slot in all_slots
                ]) <= self.problem.teacher_work_hours[teacher])

    def solve(self):
        """Returns the solved timetable"""
        solver = cp_model.CpSolver()
        solver.parameters.enumerate_all_solutions = True
        solution_printer = SchoolSchedulingSatSolutionPrinter(self.assignment, range(self.num_courses),
                                                              range(self.num_teachers),
                                                              range(self.num_slots), range(self.num_subjects),
                                                              self.problem.subjects, self.problem.teachers,
                                                              self.timeslots, self.problem.courses, 1)
        status = solver.Solve(self.model, solution_printer)
        return solution_printer.timetable


class SchoolSchedulingSatSolutionPrinter(cp_model.CpSolverSolutionCallback):
    # Finds valid solutions to the model, stops at limit that is passed
    def __init__(self, assignment, all_courses, all_teachers, all_slots, all_subjects, subjects, teachers, timeslots, courses,
                 limit):
        cp_model.CpSolverSolutionCallback.__init__(self)
        self._solution_count = 0
        self._solution_limit = limit
        self._assignment = assignment
        self._subjects = subjects
        self._teachers = teachers
        self._courses = courses
        self._timeslots = timeslots
        self._all_courses = all_courses
        self._all_teachers = all_teachers
        self._all_slots = all_slots
        self._all_subjects = all_subjects
        self.timetable = []

    def OnSolutionCallback(self):
        self._solution_count += 1
        for c in self._all_courses:
            for slot in self._all_slots:
                for s in self._all_subjects:
                    for t in self._all_teachers:
                        if self.Value(self._assignment[(c, s, t, slot)]):
                            self.timetable.append((self._courses[c], self._teachers[t], self._subjects[s], self._timeslots[slot].split()[0] , self._timeslots[slot].split()[1]))

        if self._solution_count >= self._solution_limit:
            self.StopSearch()


def create_timetable(input_classes, input_teachers, input_subjects):
    """Generates and returns a valid timetable from variables

    Arguments:
        input_classes -- List of classes
        input_teachers -- Dictionary of teachers
        input_subjects -- Dictionary of subjects
    """
    subjects = []  # List of different subjects to teach
    teaching_class = input_classes  # List of different classes
    teachers = []  # List of teachers
    teachers_work_hours = []  # Work hours of teachers per week, so 'James' works 2 hours and 'John' works 8 etc
    subjects_per_week = {}  # How many of each subject there needs to be in a week
    teachers_specialties = []  # Subject -> List of what teachers can teach what subject

    # Functions to format inputs into readable data for solver
    for teacher in input_teachers:
        teachers.append(teacher)
        teachers_work_hours.append(input_teachers[teacher][0])

    for subject in input_subjects:
        subjects.append(subject)
        subjects_per_week[subject] = input_subjects[subject]
        teachers_specialties.append([])
        for teacher in input_teachers:
            if subject == input_teachers[teacher][1]:
                teachers_specialties[-1].append(teachers.index(teacher))

    working_days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']  # Days that school is on
    periods = ['09:00:00-10:00:00', '10:00:00-11:00:00', '11:00:00-12:00:00', '13:00:00-14:00:00', '14:00:00-15:00:00']  # Time slots of each day that subjects can be in

    problem = SchoolSchedulingProblem(
        subjects, teachers, subjects_per_week, teachers_specialties, working_days,
        periods, teaching_class, teachers_work_hours)
    solver = SchoolSchedulingSatSolver(problem)
    return solver.solve()

