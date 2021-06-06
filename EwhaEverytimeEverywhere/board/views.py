from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404

from .forms import PostForm, CommentForm
from .models import Post, Comment


@login_required(login_url='login')
def post_list(request):
    posts = Post.objects.all().order_by('-created_at')
    return render(request, 'board/post_list.html',
                  {'posts': posts})


@login_required(login_url='login')
def post_detail(request, pk):
    post = get_object_or_404(Post, pk=pk)
    comments = Comment.objects.filter(post_id=pk).order_by('-comment_created')

    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment_form = form.save(commit=False)
            comment_form.post = post
            comment_form.comment_writer = request.user
            comment_form.save()
            return redirect('board:post_detail', pk=post.pk)

    else:
        form = CommentForm()
        context = {
            'post': post,
            'comments': comments,
            'comment_form': form
        }
        return render(request, 'board/post_detail.html', context)


@login_required(login_url='login')
def post_upload(request):
    if request.method == 'POST':
        form = PostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            return redirect('board:post_list')
    else:
        form = PostForm()
    return render(request, 'board/post_upload.html', {
        'form': form,
    })


@login_required(login_url='login')
def post_edit(request, pk):
    item = get_object_or_404(Post, pk=pk)
    # 그 사람 id인거 인증하는거 있어야함
    if request.method == 'POST':
        form = PostForm(instance=item)
        if form.is_valid():
            item = form.save()
            messages.success(request, '포스트를 수정했습니다.')
            return redirect(item)
    else:
        form = PostForm(instance=item)
    return render(request, 'board/post_edit.html', {
        'form': form,
    })


@login_required(login_url='login')
def post_delete(request, pk):
    post = Post.objects.get(pk=pk)
    if request.method == 'POST':
        # 그 사람 id인거 인증하는거 있어야함
        post.delete()
        messages.success(request, '포스팅을 삭제했습니다.')
        return redirect('board:post_list')

