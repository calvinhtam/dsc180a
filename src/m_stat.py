import sys
import pandas as pd
from csv import writer


# ---------------------------------------------------------------------
# Helper Functions for Getting M-Statistic
# ---------------------------------------------------------------------
def get_m_stat(rev_order, editor_order, num_edits_dict):
    # Reverses based on reading from latest revision
    rev_order = rev_order[::-1]
    editor_order = editor_order[::-1]

    # Revisions start at 1
    next_val = 1
    # Maps revision to index
    rev_map = {}
    # Tracks number of m values
    m_val_dict = {}
    # Tracks editors to who they reverted
    mutual_revs = {}
    # Tracks total number of mutual reverts
    mutual_revs_editors = set()
    max_m_val = 0

    # Iterate across the revisions
    for i in range(len(rev_order)):
        # Runs when revision is a revert
        if rev_order[i] < next_val:
            try:
                # Previous editor maps from the rev_map to the index of
                # the editor in the editor_order list, plus one for the offset
                prev_editor = editor_order[rev_map[rev_order[i]] + 1]

                # Ignore case of consecutive versions from previous edit
                if i + 1 < len(rev_order) and rev_order[i + 1] == rev_order[i]:
                    continue

                # Current editor will be at the same index as in rev_order
                curr_editor = editor_order[i]

                # Ignore case of editor reverting themselves
                if prev_editor == curr_editor:
                    continue
                # Minimum of the number of the edits between the editors
                curr_m_val = min(num_edits_dict[prev_editor],
                                 num_edits_dict[curr_editor])
                # Updates maximum value
                max_m_val = max(max_m_val, curr_m_val)

                # Adds value to a dictionary to maintain quick updates
                if curr_m_val not in m_val_dict:
                    m_val_dict[curr_m_val] = 0
                m_val_dict[curr_m_val] += 1

                # Updates E value -> number of mutual revert editors
                if curr_editor not in mutual_revs:
                    mutual_revs[curr_editor] = set()
                mutual_revs[curr_editor].add(prev_editor)
                if (prev_editor in mutual_revs and
                        curr_editor in mutual_revs[prev_editor]):
                    mutual_revs_editors.add(curr_editor)
                    mutual_revs_editors.add(prev_editor)
            except KeyError:
                continue
            except:
                e = sys.exc_info()
                print(e)
        else:
            # Maps the revision number to the index in the
            # rev_order/editor_order list
            rev_map[rev_order[i]] = i
            next_val += 1
    # Edge case when no mutual edits
    if not len(m_val_dict):
        return 0
    # Remove maximum pair(s)
    del m_val_dict[max_m_val]
    # Calculates M-Statistic
    m_stat_val = (sum([k * v for k, v in m_val_dict.items()]) *
                  len(mutual_revs_editors))
    return m_stat_val


def update_line(line, editor_mapper, editor_count, num_edits_dict,
                editor_order, rev_order):
    line = line.split()
    if line[3] not in editor_mapper:
        editor_mapper[line[3]] = editor_count
        num_edits_dict[editor_mapper[line[3]]] = 0
        editor_count += 1
    num_edits_dict[editor_mapper[line[3]]] += 1
    editor_order.append(editor_mapper[line[3]])
    rev_order.append(int(line[2]))
    return editor_count


def grab_m_stat_over_time(raw_data, data_dir='data/'):
    """
    Intended for only getting the M-Statistic over time for plotting
    Used when raw_data is just one file with the history of just one page
    :param raw_data: The raw light dump file with just one article
    :param data_dir: The directory for output
    :return: None
    """
    # File location for resulting M-Statistic over time
    page_id_write_obj = \
        open('{}out/overtime-{}'.format(
            data_dir,raw_data.split('/')[-1].replace('.txt', '.csv')),
            'w+', newline=''
        )
    page_id_fp_csv_writer = writer(page_id_write_obj)

    # Initializes for no good reason
    editor_order, num_edits_dict, editor_mapper, rev_order, editor_count = \
        [], {}, {}, [], 0

    line_num = -1
    page_id_fp_csv_writer.writerow(['Timestamp', 'M-Statistic'])
    # Iterates through each line in the light dump file
    for line in reversed(list(open(raw_data))):
        line_num += 1
        # Removes end newline characters
        line = line.rstrip()

        # Start of next page
        if '^^^' != line[:3]:
            continue

        editor_count = update_line(line, editor_mapper, editor_count,
                                   num_edits_dict, editor_order, rev_order)
        m_stat_val = get_m_stat(rev_order[::-1], editor_order[::-1],
                                num_edits_dict)
        page_id_fp_csv_writer.writerow([
            pd.to_datetime(line.split()[0][4:]), m_stat_val
            ])
    print('Done')


# ---------------------------------------------------------------------
# Driver Function for ANALYZING DATA
# ---------------------------------------------------------------------

def analyze_m_stat_data(data_dir='data/',
                        fps=
                        ("light-dump-enwiki-20200101-pages-meta-history1-" +
                         "xml-p10p1036.txt",
                         "light-dump-enwiki-20200101-pages-meta-history1-"
                         "xml-p1037p2031.txt")
                        ):

    for fp in fps:
        out_dir = '{}out/'.format(data_dir)
        # Resulting M statistic
        page_id_write_obj = \
            open(
                '{}m-stat-{}'.format(out_dir, fp.replace('light-dump-', '')),
                'w', newline=''
            )
        page_id_fp_csv_writer = writer(page_id_write_obj)

        # Maintain for page_id
        page_count = 0

        # Starter csv header
        title_id, title, m_stat_val = 'Title_ID', 'Title', 'Statistic'

        # Initializes for no good reason
        editor_order, num_edits_dict, editor_mapper, rev_order, editor_count =\
            [], {}, {}, [], 0

        line_num = -1
        # Iterates through each line in the light dump file
        for line in open(out_dir + fp):
            line_num += 1
            # Removes end newline characters
            line = line.rstrip()

            # Start of next page
            if '^^^' != line[:3]:
                if not m_stat_val:
                    m_stat_val = get_m_stat(rev_order, editor_order,
                                            num_edits_dict)
                page_id_fp_csv_writer.writerow([title_id, title, m_stat_val])

                title_id, title, m_stat_val = page_count, line, None
                page_count += 1
                if not page_count % 100000:
                    print('Done parsing', page_count, 'pages')

                editor_order, num_edits_dict, editor_mapper, rev_order = \
                    [], {}, {}, []
                editor_count = 0
                continue

            editor_count = update_line(line, editor_mapper, editor_count,
                                       num_edits_dict, editor_order, rev_order)
        if not m_stat_val:
            m_stat_val = get_m_stat(rev_order, editor_order, num_edits_dict)
            page_id_fp_csv_writer.writerow([title_id, title, m_stat_val])
        print('Done!')
