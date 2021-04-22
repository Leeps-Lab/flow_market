// color.js
// contains color definitions for 'mono' and 'rainbow' color schemes

var color_stops = {
    'red': [
        [255, 255, 255],
        [255, 0, 0],
    ],
    'gray': [
        [255, 255, 255],
        [0, 0, 0],
    ],
    'blue': [
        [255, 255, 255],
        [148, 0, 211],
    ],
    'rainbow': [
        [148, 0, 211],
        [75, 0, 130],
        [0, 0, 255],
        [0, 255, 255],
        [0, 255, 0],
        [255, 255, 0],
        [255, 127, 0],
        [255, 0, 0],
    ],
    'rainbow2': [
        [[148, 0, 211], 0.0],
        [[75, 0, 130], 0.05],
        [[0, 0, 255], 0.1],
        [[0, 255, 255], 0.15],
        [[0, 255, 0], 0.2],
        [[255, 255, 0], 0.5],
        [[255, 127, 0], 0.6],
        [[255, 0, 0], 1.0],
    ]
};

// gets colors from the gradient defined by the color stops above
// 0.0 <= percent <= 1.0
// where percent = 1.0 gets the last color in color_stops and percent = 0.0 gets the first color in color_stops
export function get_gradient_color(percent, color_scheme) {
    const scheme = color_stops[color_scheme];
    if (typeof(scheme[0][0]) == 'number') {
        percent *= (scheme.length - 1);
        const low_index = Math.floor(percent);
        const high_index = Math.ceil(percent);
        percent -= low_index;
        return [0, 1, 2].map(i => percent * scheme[high_index][i] + (1 - percent) * scheme[low_index][i]);
    }
    for (let i = 0; i < scheme.length-1; i++) {
        const curr_stop = scheme[i][1];
        const next_stop = scheme[i+1][1];
        if (percent >= curr_stop && percent <= next_stop) {
            const low_color = scheme[i][0];
            const high_color = scheme[i+1][0];
            const interp = 1 - ((percent - curr_stop) / (next_stop - curr_stop));
            return [0, 1, 2].map(i => interp * low_color[i] + (1 - interp) * high_color[i]);
        }
    }
    return scheme[scheme.length-1][0];
}
