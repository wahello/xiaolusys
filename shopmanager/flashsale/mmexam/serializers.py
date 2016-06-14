# coding=utf-8
from rest_framework import serializers
from flashsale.mmexam.models import Question, Choice


class QuestionChoiceSerialize(serializers.ModelSerializer):
    class Meta:
        model = Choice
        fields = ('choice_title', 'choice_text')


class QuestionSerialize(serializers.ModelSerializer):
    question_choice = QuestionChoiceSerialize(source='question_choices', read_only=True, many=True)

    class Meta:
        model = Question
