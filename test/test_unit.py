import pytest

from .. import mppd


@pytest.fixture()
def mips_main(monkeypatch):
    def do_main(args: list, use_main: bool = False):
        if use_main:
            monkeypatch.setattr("sys.argv", ["mppd"] + args)
            mppd.main()
        else:
            mppd.MipsProcessor(mppd.get_arg_parser().parse_args(args)).process()

    return do_main


@pytest.fixture()
def assert_result(mips_main, tmpdir, monkeypatch):
    def do_test(mips_args, input_text: str, expected_text: str, filename: str = "test", use_main: bool = False,
                pass_output_arg: bool = True):
        in_path = tmpdir.join(f"{filename}.s")
        out_path = in_path if ("-r" in mips_args or "--replace" in mips_args) else tmpdir.join(f"{filename}.out.s")

        # Write input to file
        with in_path.open("w") as f:
            f.write(input_text)

        # Run preprocessor and prettifier
        args = [str(in_path)]
        if pass_output_arg:
            args += ["-o", str(out_path)]
        args += mips_args
        mips_main(args, use_main)

        # Check result matches expected output
        with out_path.open("r") as f:
            result = f.read().strip()

        assert result == expected_text.strip()

    return do_test


def test_prettify_with_documentation(assert_result):
    assert_result(
        ["-f", "count", "-d", "-s", "-l", "-p", "-i"],
        '''
count:
    li      %max.s, 10                  # int max = 10;
count_i_init:
    li      %i, 0                       # int i = 0;
count_i_cond:
    bge     %i, %max, count_i_break     # for (i < max)
    # ...
count_i_step:
    addi    %i,%i,1                     # i++;
count_i_break:
    jr      $ra                         # return;
            ''',
        '''#########################
# count

# Frame:      $ra, $s0
# Uses:       $s0, $t0
# Clobbers:   $t0

# Locals:
#       - 'max' in $s0
#       - 'i' in $t0

# Structure:
#       - count_i_init
#       - count_i_cond
#       - count_i_step
#       - count_i_break
count:
    li        $s0, 10                               # int max = 10;
count_i_init:
    li        $t0, 0                                # int i = 0;
count_i_cond:
    bge       $t0, $s0, count_i_break               # for (i < max)
    # ...
count_i_step:
    addi      $t0, $t0, 1                           # i++;
count_i_break:
    jr        $ra                                   # return;
        ''',
        "count"
    )


def test_replace_input_file(assert_result):
    assert_result(
        ["-f", "count", "-p", "-r", "-V", "2"],
        '''
count:
    li      %max.s, 10                  # int max = 10;
            ''',
        '''count:
    li        $s0, 10                               # int max = 10;
        ''',
        "count"
    )


def test_prettify_with_spaces(assert_result):
    assert_result(
        ["-f", "count", "-p", "-r", "-S"],
        '''
count:
    li      %max.s, 10                  # int max = 10;
            ''',
        '''
count:
    li        $s0, 10                            # int max = 10;
        ''',
        "count"
    )


def test_prettify_no_tab_after_instruction(assert_result):
    assert_result(
        ["-f", "count", "-p", "-r"],
        '''
count:
    li %max.s, 10                  # int max = 10;
            ''',
        '''count:
    li        $s0, 10                               # int max = 10;
        ''',
        "count"
    )


def test_main(assert_result):
    assert_result(
        ["-f", "count", "-p", "-r", "-V", "2"],
        '''
count:
    li      %max.s, 10                  # int max = 10;
            ''',
        '''count:
    li        $s0, 10                               # int max = 10;
        ''',
        "count",
        True
    )


def test_no_output_arg(assert_result):
    assert_result(
        ["-f", "count", "-p"],
        '''
count:
    li      %max.s, 10                  # int max = 10;
            ''',
        '''count:
    li        $s0, 10                               # int max = 10;
        ''',
        "count",
        True,
        False
    )


def test_identifier_declared_before_flag(assert_result, capfd):
    assert_result(
        ["-f", "count", "-p"],
        '''
count:
    li      %max, 1            
    li      %max.s, 10                  # int max = 10;
            ''',
        '''count:
    li        $t0, 1
    li        $t0, 10                               # int max = 10;
        ''',
        "count",
        True,
        False
    )
    stdout, stderr = capfd.readouterr()
    assert "max declared before flag s" in (stdout + stderr)


def test_main_version_arg(mips_main, capfd):
    with pytest.raises(SystemExit):
        mips_main(['-v'], True)
    stdout, stderr = capfd.readouterr()
    assert stdout.startswith('v')

