import sys
import bittensor as bt
st = bt.subtensor(network='local')
print("ss58 format:",st.substrate.ss58_format)
print("current block:",st.block)

coldkey = '5HHHHHzgLnYRvnKkHd45cRUDMHXTSwx7MjUzxBrKbY4JfZWn'

# dtao epoch is 4920350

b_pre = 4920340
b_post = 4920360

n=3
if len(sys.argv)>1:
    n = int(sys.argv[1])

for i in range(n):
    s0 = st.get_stake_for_coldkey(coldkey,block=b_post+i)
    print(f'at block {b_post+i}: {s0}')
for i in range(n):
    s1 = st.query_subtensor("TotalColdkeyStake",b_pre+i,[coldkey]).value
    print(f'at block {b_pre+i}: {s1}')
for i in range(n):
    s2 = st.get_stake_for_coldkey(coldkey,block=b_post+i)
    print(f'at block {b_post+i}: {s2}')


