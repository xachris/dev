// REACT 代码笔记
// 主题: 01_useState
// 日期: 20220223

// PART 1: 导入钩子
import { useState } from "react";
import ReactDOM from "react-dom";

// PART 2: 定义组件
function Car() {

  // 设置初始状态 -- 使用解构: 使 car赋值等于对象, setCar()也传入对象)
  const [car, setCar] = useState({
    brand: "Ford",
    model: "Mustang",
    year: "1964",
    color: "red"
  });
  
  // 函数更新状态, 传入初始状态对象, 返回更新后的对象
  const updateColor = () => {
    setCar(previousState => {
      return { ...previousState, color: "blue" }    // ...previousState 表示其它不变的对象内容
    });

  // 下列代码与上方代码等效
  //   setCar(() => {
  //     return {
  //     brand: "Ford",
  //     model: "Mustang",
  //     year: "1964",
  //     color: "blue" }
  // });
  }

  return (
    <>
      <h1>My {car.brand}</h1>
      <p>
        It is a {car.color} {car.model} from {car.year}.
      </p>
      <button
        type="button"
        onClick={updateColor}
      >Blue</button>
    </>
  )
}


// PART 3: 渲染页面
ReactDOM.render(<Car />, document.getElementById('root'));
