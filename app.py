from flask import Flask, render_template, request
import os
from pysat.solvers import Glucose3

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

D = 3
N = D * D

def solve_sudoku(file_path):
    try:
        clues = []
        digits = {'0': 0, '1': 1, '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9}
        with open(file_path, "r") as f:
            for line in f.readlines():
                assert len(line.strip()) == N, "'" + line + "'"
                for c in range(0, N):
                    assert (line[c] in digits.keys() or line[c] == '.')
                clues.append(line.strip())
        assert (len(clues) == N)

        def var(r, c, v):
            assert (1 <= r and r <= N and 1 <= c and c <= N and 1 <= v and v <= N)
            return (r - 1) * N * N + (c - 1) * N + (v - 1) + 1

        cls = []  
        for r in range(1, N + 1): 
            for c in range(1, N + 1):
                cls.append([var(r, c, v) for v in range(1, N + 1)])
                for v in range(1, N + 1):
                    for w in range(v + 1, N + 1):
                        cls.append([-var(r, c, v), -var(r, c, w)])
                if len(cls[-1]) > 3:
                    cls[-1], cls[-2] = cls[-1][:3], cls[-1][3:]
                    cls.append(cls[-1][1:3] + [-var(r, c, v + 1)])
                    for i in range(3, len(cls[-2]), 2):
                        cls.append([-cls[-2][i - 1], -cls[-2][i]] + cls[-1][1:3] + [-var(r, c, v + 1)])
                        cls[-3][0] = -cls[-2][i]
        for v in range(1, N + 1):

            for r in range(1, N + 1): cls.append([var(r, c, v) for c in range(1, N + 1)])

            for c in range(1, N + 1): cls.append([var(r, c, v) for r in range(1, N + 1)])

            for sr in range(0, D):
                for sc in range(0, D):
                    cls.append([var(sr * D + rd, sc * D + cd, v)
                                for rd in range(1, D + 1) for cd in range(1, D + 1)])

        for r in range(1, N + 1):
            for c in range(1, N + 1):
                if clues[r - 1][c - 1] in digits.keys():
                    cls.append([var(r, c, digits[clues[r - 1][c - 1]])])

        dimacs_output_file = file_path + '_dimacs.txt'

        with open(dimacs_output_file, "w") as dimacs_out:
            dimacs_out.write("p cnf %d %d\n" % (N * N * N, len(cls)))
            for c in cls:
                dimacs_out.write(" ".join([str(l) for l in c]) + " 0\n")

        with Glucose3() as solver:
            for clause in cls:
                solver.add_clause(clause)

            if solver.solve():
                solution_str = ' '.join(map(str, solver.get_model()))
                grid = [['.'] * 9 for _ in range(9)]

                solution_list = [int(x) for x in solution_str.split() if int(x) > 0]

                for val in solution_list:
                    row = (val - 1) // 81
                    col = ((val - 1) % 81) // 9
                    num = (val - 1) % 9 + 1
                    grid[row][col] = str(num)

                solved_grid = ''
                for i, row in enumerate(grid):
                    if i % 3 == 0 and i != 0:
                        solved_grid += '-' * 21 + '\n'
                    solved_grid += ' '.join(row[:3]) + ' | ' + ' '.join(row[3:6]) + ' | ' + ' '.join(row[6:9]) + '\n'

                solver_output_file = file_path + '_solver.txt'
                with open(solver_output_file, "w") as solver_out:
                    solver_out.write(solution_str)

                return solved_grid
            else:
                return "No solution found."
    except Exception as e:
        return "An error occurred: " + str(e)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/return')
def return_page():
    return render_template('index.html')  

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return render_template('index.html', error='No file part')
    file = request.files['file']
    if file.filename == '':
        return render_template('index.html', error='No selected file')
    if file:
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(file_path)
        sudoku_solution = solve_sudoku(file_path)
        return render_template('solution.html', sudoku_solution=sudoku_solution)
    return render_template('index.html', error='An error occurred')

if __name__ == '__main__':
    app.run(debug=True)
