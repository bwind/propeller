from propeller import RequestHandler, Response, Template


class MailingListHandler(RequestHandler):
    def get(self, request):
        return Response(Template('mailinglist.html'))
