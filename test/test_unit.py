import pytest


from .. import mppd


@pytest.fixture()
def mips_main():
    def do_main(args: list):
        mppd.MipsProcessor(mppd.get_arg_parser().parse_args(args)).process()

    return do_main


@pytest.fixture()
def assert_result(mips_main, tmpdir):
    def do_test(mips_args, input_text: str, expected_text: str, filename: str = "test"):
        in_path = tmpdir.join(f"{filename}.s")
        out_path = tmpdir.join(f"{filename}.out.s")

        # Write input to file
        with in_path.open("w") as f:
            f.write(input_text)

        # Run preprocessor and prettifier
        mips_main([str(in_path), "-o", str(out_path)] + mips_args)

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
