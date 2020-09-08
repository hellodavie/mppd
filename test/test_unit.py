import pytest
import sys
import os
sys.path.insert(1, os.path.join(sys.path[0], '..'))


def test_prettify_adjusts_whitespace(tmpdir):
    in_name = "count.s"
    in_path = tmpdir.join(in_name)
    content = '''
count:
    li      %max.s, 10                  # int max = 10;
count_i_init:
    li      %i, 0                       # int i = 0;
count_i_cond:
    bge     %i, %max, count_i_break     # for (i < max)
    # ...
count_i_step:
    addi    %i, %i, 1                   # i++;
count_i_break:
    jr      $ra                         # return;
    '''
    with in_path.open("w") as f:
        f.write(content)
    out_name = "count.out.s"
    out_path = tmpdir.join(out_name)
    sys.argv = ['mips.py', str(in_path), "-f", "count", "-o", str(out_path), "-d", "-s", "-l", "-p"]
    import mips
    with out_path.open("r") as f:
        pass
        # assert result == expected
        # result = prettify(content)
