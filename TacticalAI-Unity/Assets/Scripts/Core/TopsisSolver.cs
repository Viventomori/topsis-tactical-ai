using System;

namespace TacticalAI.Core
{
    /// <summary>
    /// Метод TOPSIS (кроки 1–5, формули (5)–(9) статті). Усі стовпці трактуються як критерії, що
    /// максимізуються: напрям впливу критеріїв уже враховано у функціях придатності (StrategyEvaluator).
    /// Еквівалент функції topsis() у simulation/battle_sim.py.
    /// </summary>
    public static class TopsisSolver
    {
        /// <summary>Повертає коефіцієнти відносної близькості C_i для кожного рядка матриці.</summary>
        public static double[] Solve(double[][] matrix, double[] weights)
        {
            int rows = matrix.Length, cols = matrix[0].Length;
            if (weights.Length != cols) throw new ArgumentException("weights.Length must equal the number of criteria");

            double wSum = 0;
            foreach (double w in weights) wSum += w;

            // Крок 1–2: векторна нормалізація (5) та зважування (6)
            var v = new double[rows][];
            for (int i = 0; i < rows; i++) v[i] = new double[cols];
            for (int j = 0; j < cols; j++)
            {
                double den = 0;
                for (int i = 0; i < rows; i++) den += matrix[i][j] * matrix[i][j];
                den = Math.Sqrt(den);
                if (den == 0) den = 1;
                for (int i = 0; i < rows; i++) v[i][j] = matrix[i][j] / den * (weights[j] / wSum);
            }

            // Крок 3: ідеальне A+ та антиідеальне A− рішення (7)
            var best = new double[cols];
            var worst = new double[cols];
            for (int j = 0; j < cols; j++)
            {
                best[j] = double.NegativeInfinity;
                worst[j] = double.PositiveInfinity;
                for (int i = 0; i < rows; i++)
                {
                    best[j] = Math.Max(best[j], v[i][j]);
                    worst[j] = Math.Min(worst[j], v[i][j]);
                }
            }

            // Кроки 4–5: відстані (8) та коефіцієнт близькості (9)
            var c = new double[rows];
            for (int i = 0; i < rows; i++)
            {
                double dp = 0, dm = 0;
                for (int j = 0; j < cols; j++)
                {
                    dp += (v[i][j] - best[j]) * (v[i][j] - best[j]);
                    dm += (v[i][j] - worst[j]) * (v[i][j] - worst[j]);
                }
                dp = Math.Sqrt(dp);
                dm = Math.Sqrt(dm);
                c[i] = dp + dm > 0 ? dm / (dp + dm) : 0.5;
            }
            return c;
        }

        /// <summary>Зважена сума (SAW) на тій самій нормалізованій матриці — для абляційного дослідження.</summary>
        public static double[] WeightedSum(double[][] matrix, double[] weights)
        {
            int rows = matrix.Length, cols = matrix[0].Length;
            double wSum = 0;
            foreach (double w in weights) wSum += w;
            var score = new double[rows];
            for (int j = 0; j < cols; j++)
            {
                double den = 0;
                for (int i = 0; i < rows; i++) den += matrix[i][j] * matrix[i][j];
                den = Math.Sqrt(den);
                if (den == 0) den = 1;
                for (int i = 0; i < rows; i++) score[i] += matrix[i][j] / den * (weights[j] / wSum);
            }
            return score;
        }

        /// <summary>i* = arg max C_i; за рівності — перший індекс.</summary>
        public static int ArgMax(double[] c)
        {
            int best = 0;
            for (int i = 1; i < c.Length; i++)
                if (c[i] > c[best]) best = i;
            return best;
        }
    }
}
