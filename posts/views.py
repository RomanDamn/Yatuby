from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render

from .forms import PostForm, CommentForm
from .models import Group, Post, User, Follow


def index(request):
    post_list = Post.objects.all()
    paginator = Paginator(post_list, 10)

    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(
        request,
        'index.html',
        {'page': page, 'paginator': paginator}
    )


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.all()
    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(request, "group.html", {'page': page, 'paginator': paginator,
                                          'group': group})


@login_required()
def new_post(request):
    if request.method == 'POST':
        form = PostForm(request.POST, files=request.FILES or None)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            return redirect('index')
        return render(request, 'new_post.html', {'form': form})
    form = PostForm(request.POST, files=request.FILES or None)
    return render(request, 'new_post.html', {'form': form})


def profile(request, username):
    author = get_object_or_404(User, username=username)
    posts = author.posts.all()
    count = posts.count()
    paginator = Paginator(posts, 10)
    follower = Follow.objects.filter(author_id=author.id).count()
    by_follow = Follow.objects.filter(user_id=author.id).count()
    following = Follow.objects.filter(author=author)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(request, 'profile.html', {'page': page,
                                            'paginator': paginator,
                                            'count': count,
                                            'author': author,
                                            'following': following,
                                            'follower': follower,
                                            'by_follow': by_follow})


def post_view(request, username, post_id):
    post = get_object_or_404(Post, pk=post_id, author__username=username)
    author = post.author
    count = author.posts.count()
    form = CommentForm(request.POST or None)
    context = {
        'form': form,
        'author': author,
        'count': count,
        'post': post,
        'items': post.comments.all()
    }
    return render(request, 'post.html', context)


def post_edit(request, username, post_id):
    if request.user == username:
        return redirect('post', username=username, post_id=post_id)
    post = get_object_or_404(Post, author__username=username, id=post_id)
    form = PostForm(data=request.POST or None, files=request.FILES or None, instance=post)
    if form.is_valid():
        form.save()
        return redirect('post', username=username, post_id=post_id)
    return render(request, 'new_post.html',
                  {'form': form, 'post': post, 'edit': True})


def page_not_found(request, exception):
    return render(
        request,
        "misc/404.html",
        {"path": request.path},
        status=404
    )


def server_error(request):
    return render(request, "misc/500.html", status=500)


@login_required
def add_comment(request, username, post_id):
    form = CommentForm(request.POST or None)
    if form.is_valid():
        form.instance.author = request.user
        form.instance.post_id = post_id
        form.save()
    return redirect('post', username=username, post_id=post_id)


@login_required()
def follow_index(request):
    post_list = Post.objects.filter(author__following__user=request.user)
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(request, 'follow.html', {'paginator': paginator,
                                           'page': page})


@login_required
def profile_follow(request, username):
    user = User.objects.get(username=request.user)
    author = User.objects.get(username=username)
    if not user.follower.filter(author=author).exists() and user != author:
        follower = Follow.objects.create(user=user, author=author)
        follower.save()
    return redirect('profile', username=username)


@login_required
def profile_unfollow(request, username):
    follower = get_object_or_404(User, username=request.user.username)
    author = get_object_or_404(User, username=username)
    if follower.follower.filter(author=author).exists() and follower != author:
        follower.follower.get(author=author).delete()
    return redirect('profile', username=username)
