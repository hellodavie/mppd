import pytest


# These tests do not contribute to coverage,
# because coverage across sub-processes just didn't work

def remove_whitespace(s):
    return s.translate(s.maketrans('', '', ' \n\t\r'))


def test_example_count(tmpdir, run_mips):
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
    run_result = run_mips(in_path, "-f count", "-o", out_path)
    assert run_result.ret == 0
    with out_path.open("r") as f:
        result = remove_whitespace(f.read())
        expected = remove_whitespace(
            content
                .replace('.s', '')
                .replace('%max', '$s0')
                .replace('%i', '$t0')
        )
        assert result == expected
        print(result)


def test_example_count_with_documentation(tmpdir, run_mips):
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
    run_result = run_mips(in_path, "-f count", "-o", out_path, "-d", "-s", "-l")
    assert run_result.ret == 0
    with out_path.open("r") as f:
        result = remove_whitespace(f.read())
        expected = remove_whitespace(
            content
                .replace('.s', '')
                .replace('%max', '$s0')
                .replace('%i', '$t0')
        )
        # assert result == expected
        print(result)
