import csv
import ast

with open('compressed_mind2web.csv', mode='r') as infile:
    reader = csv.DictReader(infile)
    rows = list(reader)


for row in rows:
    obs = row['obs'].split('\n')
    windowed_obs = ast.literal_eval(row['windowed_obs'])
    bounded_obs = ast.literal_eval(row['bounded_obs'])
    new_windowed_obs = "\n".join(windowed_obs)
    new_bounded_obs = "\n".join(bounded_obs)
    action = row['action'].split(' ')[-1]

    compression_rate_adj = len(windowed_obs) / len(obs)
    compression_rate_bound = len(bounded_obs) / len(obs)
    raw_compression_rate_adj = len(new_windowed_obs) / len(row['obs'])
    raw_compression_rate_bound = len(new_bounded_obs) / len(row['obs'])

    correct_count_adj = 1 if action in new_windowed_obs else 0
    correct_count_bound = 1 if action in new_bounded_obs else 0


    row['windowed_obs'] = windowed_obs
    row['bounded_obs'] = bounded_obs
    row['compression_rate_adj'] = compression_rate_adj
    row['compression_rate_bound'] = compression_rate_bound
    row['correct_count_adj'] = correct_count_adj
    row['correct_count_bound'] = correct_count_bound
    row['new_windowed_obs'] = new_windowed_obs
    row['new_bounded_obs'] = new_bounded_obs
    row['raw_compression_rate_adj'] = raw_compression_rate_adj
    row['raw_compression_rate_bound'] = raw_compression_rate_bound


recall_adj = sum([row['correct_count_adj'] for row in rows]) / len(rows)
recall_bound = sum([row['correct_count_bound'] for row in rows]) / len(rows)

with open(f'1106_mind2web_adj{recall_adj:.2f}_bd{recall_bound:.2f}.csv', mode='w', newline='') as outfile:
    writer = csv.DictWriter(outfile, fieldnames=rows[0].keys())
    writer.writeheader()
    writer.writerows(rows)
