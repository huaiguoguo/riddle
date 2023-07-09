from typing import List


class DiceCmdCalculator:
    def __init__(self, dice_onec_value, dice_twice_value, dice_thirce_value):
        self.dice_onec_value = dice_onec_value
        self.dice_twice_value = dice_twice_value
        self.dice_thirce_value = dice_thirce_value
        self.dice_total = dice_onec_value + dice_twice_value + dice_thirce_value

    def is_consecutive(self) -> List[int] | bool:
        nums = [self.dice_onec_value, self.dice_twice_value, self.dice_thirce_value]
        if not all(isinstance(num, int) and num > 0 for num in nums):
            raise ValueError("所有参数应该为正整数.")
        # nums.sort()
        if all(a + 1 == b for a, b in zip(nums, nums[1:])):
            return nums
        else:
            return False

    def is_consecutive_bak(*nums: int) -> List[int] | bool:
        if not all(isinstance(num, int) and num > 0 for num in nums):
            raise ValueError("All arguments should be positive integers.")

        nums = list(nums)
        nums.sort()
        if max(nums) - min(nums) == len(nums) - 1:
            return nums
        else:
            return False

    def has_duplicates(self) -> bool:
        nums = [self.dice_onec_value, self.dice_twice_value, self.dice_thirce_value]
        if not all(isinstance(num, int) and num > 0 for num in nums):
            raise ValueError("所有参数应该为正整数.")
        return len(nums) != len(set(nums))

    def whether_leopard(self, bet_cmd):
        if self.dice_total in [3, 18] or (self.dice_total in [6, 9, 12, 15] and self.dice_onec_value == self.dice_twice_value == self.dice_thirce_value):  # 豹子
            bet_cmd.append('豹子')

    def whether_duplicates(self, bet_cmd) -> None:
        if self.has_duplicates():
            bet_cmd.append('对子')

    def whether_consecutive(self, bet_cmd):
        if self.is_consecutive():
            bet_cmd.append('顺子')

    def getcmd_by_dice_value(self, is_hist: bool = False) -> List[str]:
        small_even = [i for i in range(3, 10) if i % 2 == 0]  # [4, 6, 8]
        small_odd = [i for i in range(3, 10) if i % 2 != 0]  # [3, 5, 7, 9]
        big_even = [i for i in range(10, 18) if i % 2 == 0]  # [10, 12, 14, 16]
        big_odd = [i for i in range(10, 18) if i % 2 != 0]  # [11, 13, 15, 17]

        bet_cmd = []
        if self.dice_total in small_even:  # 小, 双, 小双
            bet_cmd = ['小', '双', '小双']
        elif self.dice_total in small_odd:  # 小, 单, 小单
            bet_cmd = ['小', '单', '小单']
        elif self.dice_total in big_even:  # 大, 双, 大双
            bet_cmd = ['大', '双', '大双']
        elif self.dice_total in big_odd:  # 大, 单, 大单
            bet_cmd = ['大', '单', '大单']

        if is_hist:
            bet_cmd.pop()

        # 豹子
        self.whether_leopard(bet_cmd)

        # 检测对子
        if '豹子' not in bet_cmd:
            self.whether_duplicates(bet_cmd)

        # 顺子
        self.whether_consecutive(bet_cmd)

        return bet_cmd

    def getcmd_by_dice_value_to_history(self, is_single: bool = True) -> List[str]:
        return self.getcmd_by_dice_value(is_hist=True)
