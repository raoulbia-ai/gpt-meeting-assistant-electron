const path = require('path');

module.exports = {
  mode: 'development',
  entry: './src/renderer.js',
  output: {
    path: path.resolve(__dirname, 'dist'),
    filename: 'bundle.js'
  },
  module: {
    rules: [
      {
        test: /\.jsx?$/,
        exclude: /node_modules/,
        use: {
          loader: 'babel-loader',
          options: {
            presets: ['@babel/preset-env', '@babel/preset-react']
          }
        }
      }, // End of JSX rule
      { // Start of CSS rule
        test: /\.css$/,
        use: ['style-loader', 'css-loader']
      } // End of CSS rule
    ]
  },
  resolve: {
    extensions: ['.js', '.jsx']
  }
};