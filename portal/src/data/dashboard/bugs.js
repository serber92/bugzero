export const days = ['Mon', 'Tues', 'Wed', 'Thurs', 'Fri', 'Sat', 'Sun'];

export const bugsByDays = {
  all: [4, 1, 6, 2, 7, 12, 4].map(d => (d * 3.14).toFixed(2)),
  cisco: [3, 1, 4, 5, 5, 9, 6].map(d => (d * 3.14).toFixed(2)),
  hpe: [3, 1, 4, 2, 5, 9, 0].map(d => (d * 3.14).toFixed(2)),
  rh: [3, 1, 4, 3, 5, 9, 7].map(d => (d * 3.14).toFixed(2)),
  msft: [4, 6, 3, 1, 5, 9, 1].map(d => (d * 3.14).toFixed(2)),
  vmware: [1, 2, 4, 4, 5, 3, 2].map(d => (d * 3.14).toFixed(2))
};
