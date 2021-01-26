import pytest
from sys import executable

from pathlib import Path

SCRIPT_RELATIVE_PATH = "../mppd.py"
SCRIPT_PATH = Path(__file__).parent / SCRIPT_RELATIVE_PATH


@pytest.fixture
def run_mips(testdir):
    def do_run(*args):
        args = [executable, SCRIPT_PATH] + list(args)
        return testdir.run(*args)

    return do_run


def test_example_count(tmpdir, run_mips, util):
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
        result = util.remove_whitespace(f.read())
        expected = util.remove_whitespace(
            content
                .replace('.s', '')
                .replace('%max', '$s0')
                .replace('%i', '$t0')
        )
        assert result == expected


def test_example_count_with_documentation(tmpdir, run_mips, util):
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
        result = util.remove_whitespace(f.read())
    expected = util.remove_whitespace(
        '''#########################
        #count
        #Frame:$ra,$s0
        #Uses:$s0,$t0
        #Clobbers:$t0
        #Locals:
        #-'max'in$s0
        #-'i'in$t0
        #Structure:
        #-count_i_init
        #-count_i_cond
        #-count_i_step
        #-count_i_break
        count:
        li$s0,10#intmax=10;
        count_i_init:
        li$t0,0#inti=0;
        count_i_cond:
        bge$t0,$s0,count_i_break#for(i<max)
        #...
        count_i_step:
        addi$t0,$t0,1#i++;
        count_i_break:
        jr$ra#return;''')
    assert result == expected
