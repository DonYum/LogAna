from flask import jsonify, request, g, url_for, current_app
from .. import db
# from ..models import Post, Permission, Comment
from . import api
# from .decorators import permission_required


@api.route('/test', methods=['GET'])
def get_test():
    # page = request.args.get('page', 1, type=int)
    # pagination = Comment.query.order_by(Comment.timestamp.desc()).paginate(
    #     page, per_page=current_app.config['FLASKY_COMMENTS_PER_PAGE'],
    #     error_out=False)
    # comments = pagination.items
    # prev = None
    # if pagination.has_prev:
    #     prev = url_for('api.get_comments', page=page-1, _external=True)
    # next = None
    # if pagination.has_next:
    #     next = url_for('api.get_comments', page=page+1, _external=True)
    return jsonify({
        'data': "hello"
    })


# @api.route('/comments/<int:id>')
# def get_comment(id):
#     comment = Comment.query.get_or_404(id)
#     return jsonify(comment.to_json())

