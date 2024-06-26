# 网格分离助手
这是一个配合[网格组管理脚本](https://www.caimogu.cc/post/1081209.html)的blender插件，能够帮你把网格拆成许多碎片，用于制作怪猎曙光mod。

插件执行时间可能需要十几秒，为避免造成不可挽回的损失，

**使用前记得存档！**

**使用前记得存档！**

**使用前记得存档！**

## 第一步：分离预览
选中一个网格，设置参数，然后点击`分离预览`。插件会用缝合边来标记分离结果。

对于一些复杂且面数多的模型，如下图安卡希雅的衣服，上面有很多小饰品，每个小饰品还由一个或多个松散块组成。

![1.png](https://github.com/dddder4/Split-Mesh-Helper/blob/main/image/1.png)

让插件划分这些小饰品会产生很多组数，可能会导致组数超出上限。所以我按松散块分离，然后只挑出大块的作为主体，合并后对主体用插件。小饰品之间按需求互相合并，然后可以先放着不管，最后再来处理它们。当然你可以先不处理让插件划分试试，不行再来拆。下图只是展示分离结果，不需要移动，左边是小饰品，右边是主体。

![2.png](https://github.com/dddder4/Split-Mesh-Helper/blob/main/image/2.png)

### 1、预期组数
指你希望插件把模型划分成多少份，数字越大越不准确，我建议可以先给个100看看，再进行微调。安卡希雅的衣服主体大概3万个面，我给的120。

### 2、最大组数
在预览执行过程中如果超过最大组数则会停止划分并清除所有缝合边，你可以根据需求设置。Reframework里记录的曙光最大Group编号是254。

### 3、分离预览
点击`分离预览`，插件在每次打开blender后第一次使用`分离预览`时会尝试打开控制台以显示进度，但是blender提供的`切换系统控制台`非常不好用，如果已经打开了控制台则会关闭。

![3.png](https://github.com/dddder4/Split-Mesh-Helper/blob/main/image/3.png)

接下来插件会清除模型原来的缝合边，在模型上标记新的缝合边用于第二步的分离。

![4.png](https://github.com/dddder4/Split-Mesh-Helper/blob/main/image/4.png)

上图可以看到安卡希雅背后的两条带子一大块都没有划分，我想再分细点，就单独分离出来，单独设置参数，再进行`分离预览`。下图是单独使用`分离预览`后的结果。

![5.png](https://github.com/dddder4/Split-Mesh-Helper/blob/main/image/5.png)

带子和主体合并，最后的效果如下。一些标得不好看的缝合边可以自己增删改，确认无误后进行第二步。

![6.png](https://github.com/dddder4/Split-Mesh-Helper/blob/main/image/6.png)

## 第二步：确认分离
选中一个网格，设置一堆参数，然后点击`确认分离`。插件不会破坏原模型，而是复制一份出来处理。

### 1、排序方向
用来规定模型消失或出现的大致方向。安卡希雅衣服要从下往上消失，因此我选`-Z到Z`。

### 2、反向
反转排序方向。`-X到X`变成`X到-X`，其他同理。

### 3、轴细分
用来规定模型消失或出现的随机。确定好一个排序方向后，可以对剩下两个坐标轴做细分，细分的目标是模型的边界范围。

![7.png](https://github.com/dddder4/Split-Mesh-Helper/blob/main/image/7.png)

我XY细分给的2，那么俯视图看起来会像这个样子，和细分一个方块一样。

![8.png](https://github.com/dddder4/Split-Mesh-Helper/blob/main/image/8.png)

这样边界范围就被划分成了9个区域，在下文点击`确定分离`后，插件会对每个区域生成一行Rule并打印在控制台。把它们复制到json文件，就能实现[网格组管理脚本](https://www.caimogu.cc/post/1081209.html)在每次触发判定时，从9个区域内随机挑选一个区域，再执行消失或出现。

### 4、重命名
#### 4.1、开始组号
对应Group后面的数字。开始组号在重命名时会不断递增。

#### 4.2、材质编号
对应Sub后面的数字。材质编号在重命名时不变。

#### 4.3、材质名称
对应双下划线之后的材质名称。材质名称在重命名时不变。

### 5、确定分离
点击`确定分离`，插件会新建两个集合存放分离结果。

![9.png](https://github.com/dddder4/Split-Mesh-Helper/blob/main/image/9.png)

Split Mesh Result里存放的是带骨架的分离结果，而Split Mesh Loose里存放的是不带骨架的松散块网格。Result里的网格会添加数据传递修改器来消除模型接缝，对象就是Loose里面的网格。数据传递修改器要放在骨架修改器之后，而且不需要应用，除非你知道你在干什么，否则不要动它们。

控制台会输出根据参数生成的Rule，可以直接复制拿走。

![10.png](https://github.com/dddder4/Split-Mesh-Helper/blob/main/image/10.png)

## 额外
一些用来修补小问题的额外功能。

### 1、合并骨架
如果你对多个网格分别使用了`确定分离`生成了多个骨架，又想把它们整合到一个骨架里，可以用这个功能。

需要选中至少两个骨架。插件会把选中骨架下面的网格移到激活骨架下面。网格必须要有名为"split_mesh_modifier"的修改器，通常情况下是插件分离时自动添加的数据传递修改器。

### 2、重命名
需要选中至少一个网格。把选中网格按照`开始组号`、`材质编号`、`材质名称`填写的内容进行重命名。

我还有安卡希雅衣服分离出来的小饰品没有处理，选中它们，换绑骨架。

![11.png](https://github.com/dddder4/Split-Mesh-Helper/blob/main/image/11.png)

选中骨架下所有需要重命名的网格，点击`重命名`。重命名后的Rule会打印在控制台。

![12.png](https://github.com/dddder4/Split-Mesh-Helper/blob/main/image/12.png)
