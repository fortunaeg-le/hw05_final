from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import (
    require_http_methods,
    require_GET,
    require_POST)

from .forms import PostForm, CommentForm
from .models import Group, Post, Follow

User = get_user_model()


@require_http_methods(["GET"])
def index(request):

    template = 'posts/index.html'
    posts = Post.objects.all()

    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {'page_obj': page_obj}

    return render(request, template, context)


@require_GET
def group_posts(request, slug):

    template = 'posts/group_list.html'
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.all()

    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'group': group,
        'page_obj': page_obj,
    }

    return render(request, template, context=context)


@require_GET
def profile(request, username):

    template = 'posts/profile.html'
    author = get_object_or_404(User, username=username)
    posts = author.posts.all()
    count = posts.count()

    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    following = False
    if request.user.is_authenticated:
        following = Follow.objects.filter(
            user=request.user,
            author=author,
        )
    i_not_auth = True
    if request.user == author:
        i_not_auth = False
    context = {
        'author': author,
        'following': following,
        'page_obj': page_obj,
        'count': count,
        'i_not_auth': i_not_auth,
    }
    return render(request, template, context)


@require_http_methods(["GET", "POST"])
def post_detail(request, post_id):

    template = 'posts/post_detail.html'
    post = get_object_or_404(Post, pk=post_id)
    comments = post.comments.all()
    form = CommentForm()
    context = {
        'post': post,
        'form': form,
        'comments': comments,
    }
    return render(request, template, context)


@login_required
@require_http_methods(["GET", "POST"])
def post_create(request):
    context = {
        'form': None,
        'is_edit': False,
    }
    template = 'posts/create_post.html'
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
    )
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('posts:profile', request.user.username)
    context['form'] = form
    return render(request, template, context)


@login_required
@require_http_methods(["GET", "POST"])
def post_edit(request, post_id):
    template = 'posts/create_post.html'
    post = get_object_or_404(Post, pk=post_id)
    if post.author != request.user:
        return redirect('posts:post_detail', post.pk)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post)
    if form.is_valid():
        post.save()
        return redirect('posts:post_detail', post.pk)
    context = {
        'is_edit': True,
        'post': post,
        'form': form
    }
    return render(request, template, context)


@login_required
@require_POST
def add_comment(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
@require_GET
def follow_index(request):
    template = 'posts/follow.html'
    posts = Post.objects.filter(
        author__following__user=request.user
    )
    post_exists = posts.exists()
    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'post_exists': post_exists,
        'page_obj': page_obj
    }
    return render(request, template, context)


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    if request.user == author:
        return redirect('posts:profile', author)
    if Follow.objects.filter(user=request.user, author=author).exists():
        return redirect('posts:profile', username=username)
    Follow.objects.create(
        author=author,
        user=request.user,
    )
    return redirect('posts:profile', username=username)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    if request.user == author:
        return redirect('posts:profile', username=username)
    if not Follow.objects.filter(user=request.user, author=author).exists():
        return redirect('posts:profile', username=username)
    follow = get_object_or_404(
        Follow,
        author=author,
        user=request.user,
    )
    follow.delete()
    return redirect('posts:profile', username=username)
