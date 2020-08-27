import numpy as np

class scan_test():

    def generate_scan_range_test(self, dimension=1):
        do_scan = dimension % 2 == 0
        scan_start = dimension
        scan_end = 2*dimension
        scan_step_size = 1
        parameter = 'test_'+str(dimension)
        return do_scan, scan_start, scan_end+scan_step_size, scan_step_size, parameter

    def generate_scan_dictionary(self, n):
        # Generate all scanning data
        scancombineddata = [self.generate_scan_range_test(i) for i in range(1,n+1)]
        # Count Trues to find number of dimensions
        ndims = np.sum([s[0] for s in scancombineddata])
        # Select data where do_scan is True
        scan_data = [s for s in scancombineddata if s[0] is True]
        # Generate slice indexes based on selected data
        idx = tuple(slice(s[1], s[2], s[3]) for s in scan_data)
        # Generate values for each dimension
        grid = np.mgrid[idx].reshape(ndims,-1).T
        # get list of params
        params = [scan[4] for scan in scan_data]
        # for each param generate correct length of list, then transpose them a 
        # few times to get in [[param1, value1], [param2, value2]...] blocks for each step of the scan
        return [list(zip(*a)) for a in zip(*[[params for i in range(len(grid))], grid])]

test = scan_test()
grid = test.generate_scan_dictionary(4)
print(grid)
